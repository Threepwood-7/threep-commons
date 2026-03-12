"""Windows storage identity and capacity helpers."""

from __future__ import annotations

import ctypes
import os
import shutil
from contextlib import suppress
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path

from ...fs_paths import path_key
from .volumes import (
    get_volume_guid_path,
    get_volume_mount_point,
    list_logical_drive_roots,
    list_mounted_volume_paths,
)

_DWORD_SIZE = ctypes.sizeof(wintypes.DWORD)

if os.name == "nt":
    _KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)

    _CREATE_FILE = _KERNEL32.CreateFileW
    _CREATE_FILE.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    _CREATE_FILE.restype = wintypes.HANDLE

    _DEVICE_IO_CONTROL = _KERNEL32.DeviceIoControl
    _DEVICE_IO_CONTROL.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    _DEVICE_IO_CONTROL.restype = wintypes.BOOL

    _CLOSE_HANDLE = _KERNEL32.CloseHandle
    _CLOSE_HANDLE.argtypes = [wintypes.HANDLE]
    _CLOSE_HANDLE.restype = wintypes.BOOL

    _GET_VOLUME_INFORMATION = _KERNEL32.GetVolumeInformationW
    _GET_VOLUME_INFORMATION.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPWSTR,
        wintypes.DWORD,
    ]
    _GET_VOLUME_INFORMATION.restype = wintypes.BOOL

    _FILE_SHARE_READ = 0x00000001
    _FILE_SHARE_WRITE = 0x00000002
    _FILE_SHARE_DELETE = 0x00000004
    _OPEN_EXISTING = 3
    _INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
    _ERROR_MORE_DATA = 234
    _ERROR_INSUFFICIENT_BUFFER = 122
    _IOCTL_VOLUME_GET_VOLUME_DISK_EXTENTS = 0x00560000

    class _DiskExtent(ctypes.Structure):
        _fields_ = [
            ("DiskNumber", wintypes.DWORD),
            ("StartingOffset", ctypes.c_longlong),
            ("ExtentLength", ctypes.c_longlong),
        ]

    class _VolumeDiskExtents(ctypes.Structure):
        _fields_ = [
            ("NumberOfDiskExtents", wintypes.DWORD),
            ("Extents", _DiskExtent * 1),
        ]

    _VOLUME_DISK_EXTENTS_EXTENTS_OFFSET = _VolumeDiskExtents.Extents.offset
    _DISK_EXTENT_SIZE = ctypes.sizeof(_DiskExtent)


@dataclass(frozen=True, slots=True)
class WindowsStorageUsage:
    root_path: Path
    volume_identity: str
    volume_label: str
    disk_tokens: set[str]
    bytes_used: int
    bytes_total: int


def is_local_windows_path(path: str) -> bool:
    return not str(path).startswith("\\\\")


def resolve_volume_identity(path: str | Path) -> str:
    normalized = str(Path(path))
    if os.name == "nt":
        try:
            volume_guid_path = get_volume_guid_path(normalized)
            return f"volume:{volume_guid_path.casefold()}"
        except OSError:
            pass
    try:
        return f"dev:{int(os.stat(normalized).st_dev)}"
    except OSError:
        anchor = Path(normalized).anchor or normalized
        return f"path:{anchor.casefold()}"


def _parse_disk_numbers_from_volume_extents_payload(
    payload: bytes,
    extent_count: int,
    *,
    extent_size: int,
    extents_offset: int,
) -> set[int]:
    disks: set[int] = set()
    for idx in range(max(0, int(extent_count))):
        start = int(extents_offset) + (idx * int(extent_size))
        end = start + int(_DWORD_SIZE)
        if end > len(payload):
            raise OSError("Volume disk extent payload ended unexpectedly")
        disks.add(int.from_bytes(payload[start:end], "little"))
    return disks


def _query_volume_disk_extents(volume_guid_path: str) -> bytes:
    if os.name != "nt":
        raise OSError(
            f"Windows disk extent API is unavailable on this platform: {volume_guid_path}"
        )

    handle = _CREATE_FILE(
        volume_guid_path.rstrip("\\"),
        0,
        _FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE,
        None,
        _OPEN_EXISTING,
        0,
        None,
    )
    if handle == _INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        size = 4096
        max_size = 1 << 20
        while size <= max_size:
            out_buffer = ctypes.create_string_buffer(size)
            bytes_returned = wintypes.DWORD(0)
            ok = _DEVICE_IO_CONTROL(
                handle,
                _IOCTL_VOLUME_GET_VOLUME_DISK_EXTENTS,
                None,
                0,
                out_buffer,
                size,
                ctypes.byref(bytes_returned),
                None,
            )
            if not ok:
                err = ctypes.get_last_error()
                if err in (_ERROR_MORE_DATA, _ERROR_INSUFFICIENT_BUFFER):
                    size *= 2
                    continue
                raise ctypes.WinError(err)
            if bytes_returned.value < int(_VOLUME_DISK_EXTENTS_EXTENTS_OFFSET):
                raise OSError("No disk extent data returned")
            count = int.from_bytes(out_buffer.raw[: int(_DWORD_SIZE)], "little")
            if count <= 0:
                raise OSError("Volume has no disk extents")
            needed = int(_VOLUME_DISK_EXTENTS_EXTENTS_OFFSET) + (
                int(_DISK_EXTENT_SIZE) * count
            )
            if bytes_returned.value < needed:
                size = max(size * 2, needed)
                continue
            return out_buffer.raw[: int(bytes_returned.value)]
        raise OSError("Volume disk extent query output exceeded supported buffer sizes")
    finally:
        _CLOSE_HANDLE(handle)


def resolve_physical_disk_numbers(path: str | Path) -> set[int]:
    if os.name != "nt":
        raise OSError(
            f"Windows disk extent API is unavailable on this platform: {path}"
        )

    payload = _query_volume_disk_extents(get_volume_guid_path(path))
    count = int.from_bytes(payload[: int(_DWORD_SIZE)], "little")
    disks = _parse_disk_numbers_from_volume_extents_payload(
        payload,
        count,
        extent_size=int(_DISK_EXTENT_SIZE),
        extents_offset=int(_VOLUME_DISK_EXTENTS_EXTENTS_OFFSET),
    )
    if disks:
        return disks
    raise OSError("Volume disk extent query returned no disk numbers")


def resolve_physical_disk_tokens(path: str | Path) -> set[str]:
    if os.name == "nt":
        disks = resolve_physical_disk_numbers(path)
        if not disks:
            raise OSError("No physical disks found for volume")
        return {f"disk:{disk}" for disk in sorted(disks)}
    return {f"dev:{int(os.stat(str(Path(path))).st_dev)}"}


def _volume_label_for_root(root: Path) -> str:
    if os.name != "nt":
        raise OSError(
            f"Windows volume metadata API is unavailable on this platform: {root}"
        )

    volume_name = ctypes.create_unicode_buffer(1024)
    file_system_name = ctypes.create_unicode_buffer(1024)
    serial_number = wintypes.DWORD(0)
    max_component_length = wintypes.DWORD(0)
    file_system_flags = wintypes.DWORD(0)
    ok = _GET_VOLUME_INFORMATION(
        str(get_volume_mount_point(root)),
        volume_name,
        len(volume_name),
        ctypes.byref(serial_number),
        ctypes.byref(max_component_length),
        ctypes.byref(file_system_flags),
        file_system_name,
        len(file_system_name),
    )
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())
    return str(volume_name.value).strip()


def list_windows_storage_roots() -> list[Path]:
    if os.name != "nt":
        return []

    candidates: list[Path] = []
    with suppress(OSError):
        candidates.extend(list_logical_drive_roots())
    with suppress(OSError):
        candidates.extend(list_mounted_volume_paths())

    normalized: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not is_local_windows_path(str(candidate)):
            continue
        root = Path(candidate)
        try:
            root = get_volume_mount_point(root)
        except OSError:
            drive = Path(root).drive
            if drive:
                root = Path(f"{drive}\\")
        if not os.path.isdir(root):
            continue
        key = path_key(root)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(root)
    return normalized


def list_windows_storage_usage() -> list[WindowsStorageUsage]:
    if os.name != "nt":
        return []

    entries: list[WindowsStorageUsage] = []
    for root in list_windows_storage_roots():
        try:
            usage = shutil.disk_usage(root)
        except OSError:
            continue
        total = int(usage.total)
        if total <= 0:
            continue
        free = min(int(usage.free), total)
        used = max(0, total - free)
        volume_identity = resolve_volume_identity(root)
        try:
            disk_tokens = resolve_physical_disk_tokens(root)
        except OSError:
            disk_tokens = {volume_identity}
        try:
            volume_label = _volume_label_for_root(root)
        except OSError:
            volume_label = ""
        entries.append(
            WindowsStorageUsage(
                root_path=root,
                volume_identity=volume_identity,
                volume_label=volume_label,
                disk_tokens=set(disk_tokens),
                bytes_used=used,
                bytes_total=total,
            )
        )
    return entries


__all__ = [
    "WindowsStorageUsage",
    "is_local_windows_path",
    "list_windows_storage_roots",
    "list_windows_storage_usage",
    "resolve_physical_disk_numbers",
    "resolve_physical_disk_tokens",
    "resolve_volume_identity",
]
