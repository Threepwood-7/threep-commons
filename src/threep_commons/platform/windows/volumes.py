"""Thin Win32 wrappers for volume and mount-point enumeration."""

from __future__ import annotations

import os
from pathlib import Path

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    _KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)

    _GET_VOLUME_PATH_NAME = _KERNEL32.GetVolumePathNameW
    _GET_VOLUME_PATH_NAME.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    _GET_VOLUME_PATH_NAME.restype = wintypes.BOOL

    _GET_LOGICAL_DRIVES = _KERNEL32.GetLogicalDrives
    _GET_LOGICAL_DRIVES.argtypes = []
    _GET_LOGICAL_DRIVES.restype = wintypes.DWORD

    _GET_VOLUME_NAME_FOR_MOUNT = _KERNEL32.GetVolumeNameForVolumeMountPointW
    _GET_VOLUME_NAME_FOR_MOUNT.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    _GET_VOLUME_NAME_FOR_MOUNT.restype = wintypes.BOOL

    _GET_VOLUME_PATH_NAMES_FOR_VOLUME_NAME = _KERNEL32.GetVolumePathNamesForVolumeNameW
    _GET_VOLUME_PATH_NAMES_FOR_VOLUME_NAME.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    _GET_VOLUME_PATH_NAMES_FOR_VOLUME_NAME.restype = wintypes.BOOL

    _FIND_FIRST_VOLUME = _KERNEL32.FindFirstVolumeW
    _FIND_FIRST_VOLUME.argtypes = [wintypes.LPWSTR, wintypes.DWORD]
    _FIND_FIRST_VOLUME.restype = wintypes.HANDLE

    _FIND_NEXT_VOLUME = _KERNEL32.FindNextVolumeW
    _FIND_NEXT_VOLUME.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD]
    _FIND_NEXT_VOLUME.restype = wintypes.BOOL

    _FIND_VOLUME_CLOSE = _KERNEL32.FindVolumeClose
    _FIND_VOLUME_CLOSE.argtypes = [wintypes.HANDLE]
    _FIND_VOLUME_CLOSE.restype = wintypes.BOOL

    _INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
    _ERROR_MORE_DATA = 234
    _ERROR_INSUFFICIENT_BUFFER = 122
    _ERROR_NO_MORE_FILES = 18


def _require_windows(detail: str) -> OSError:
    return OSError(f"Windows volume API is unavailable on this platform: {detail}")


def _coerce_path_text(path: str | Path) -> str:
    return os.path.abspath(str(Path(path)))


def _ensure_trailing_backslash(value: str) -> str:
    if value and not value.endswith("\\"):
        return f"{value}\\"
    return value


def _parse_volume_path_multi_string(raw: str) -> list[Path]:
    return [Path(_ensure_trailing_backslash(item)) for item in raw.split("\x00") if item]


def get_volume_mount_point(path: str | Path) -> Path:
    if os.name != "nt":
        raise _require_windows(str(path))

    normalized = _coerce_path_text(path)
    mount_point = ctypes.create_unicode_buffer(4096)
    if not _GET_VOLUME_PATH_NAME(normalized, mount_point, len(mount_point)):
        raise ctypes.WinError(ctypes.get_last_error())
    return Path(_ensure_trailing_backslash(str(mount_point.value)))


def get_volume_guid_path(path: str | Path) -> str:
    if os.name != "nt":
        raise _require_windows(str(path))

    mount = _ensure_trailing_backslash(str(get_volume_mount_point(path)))
    volume = ctypes.create_unicode_buffer(4096)
    if not _GET_VOLUME_NAME_FOR_MOUNT(mount, volume, len(volume)):
        raise ctypes.WinError(ctypes.get_last_error())
    return str(volume.value)


def _query_volume_path_names(volume_guid_path: str) -> str:
    if os.name != "nt":
        raise _require_windows(volume_guid_path)

    size = 512
    max_size = 1 << 20
    while size <= max_size:
        buffer = ctypes.create_unicode_buffer(size)
        required = wintypes.DWORD(0)
        ok = _GET_VOLUME_PATH_NAMES_FOR_VOLUME_NAME(
            volume_guid_path,
            buffer,
            size,
            ctypes.byref(required),
        )
        if ok:
            return ctypes.wstring_at(buffer, size)
        err = ctypes.get_last_error()
        if err in (_ERROR_MORE_DATA, _ERROR_INSUFFICIENT_BUFFER):
            size = max(size * 2, int(required.value) + 1)
            continue
        raise ctypes.WinError(err)
    raise OSError("Windows mount-point query exceeded supported buffer sizes")


def list_volume_mount_points(volume_guid_path: str) -> list[Path]:
    if os.name != "nt":
        raise _require_windows(volume_guid_path)
    return _parse_volume_path_multi_string(_query_volume_path_names(volume_guid_path))


def list_mounted_volume_paths() -> list[Path]:
    if os.name != "nt":
        raise _require_windows("mounted volume enumeration")

    volume = ctypes.create_unicode_buffer(4096)
    handle = _FIND_FIRST_VOLUME(volume, len(volume))
    if handle == _INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error())

    mounts: list[Path] = []
    try:
        while True:
            volume_guid_path = str(volume.value)
            mounts.extend(list_volume_mount_points(volume_guid_path))
            ok = _FIND_NEXT_VOLUME(handle, volume, len(volume))
            if ok:
                continue
            err = ctypes.get_last_error()
            if err == _ERROR_NO_MORE_FILES:
                break
            raise ctypes.WinError(err)
        return mounts
    finally:
        _FIND_VOLUME_CLOSE(handle)


def list_logical_drive_roots() -> list[Path]:
    if os.name != "nt":
        raise _require_windows("logical drive enumeration")

    bitmask = int(_GET_LOGICAL_DRIVES())
    return [
        Path(f"{chr(ord('A') + index)}:\\")
        for index in range(26)
        if bitmask & (1 << index)
    ]


__all__ = [
    "get_volume_guid_path",
    "get_volume_mount_point",
    "list_logical_drive_roots",
    "list_mounted_volume_paths",
    "list_volume_mount_points",
]

