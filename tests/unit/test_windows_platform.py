from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from threep_commons.fs_paths import path_key
from threep_commons.platform.windows import storage, volumes


def test_parse_volume_path_multi_string_returns_paths() -> None:
    paths = volumes._parse_volume_path_multi_string("C:\\\x00C:\\mount\\disk1\x00\x00")
    assert paths == [Path("C:\\"), Path("C:\\mount\\disk1")]


def test_query_volume_path_names_grows_buffer_on_more_data(monkeypatch) -> None:
    if not hasattr(volumes, "ctypes"):
        pytest.skip("Windows ctypes bindings are unavailable on this platform")

    state = {"calls": 0}

    def _fake_query(_name, buffer, size, required):
        state["calls"] += 1
        if state["calls"] == 1:
            required._obj.value = 32
            return False
        text = "C:\\\x00C:\\mount\\disk1\x00\x00"
        for index, char in enumerate(text):
            buffer[index] = char
        return True

    monkeypatch.setattr(volumes, "_GET_VOLUME_PATH_NAMES_FOR_VOLUME_NAME", _fake_query)
    monkeypatch.setattr(volumes.ctypes, "get_last_error", lambda: volumes._ERROR_MORE_DATA)

    raw = volumes._query_volume_path_names("\\\\?\\Volume{abc}\\")

    assert raw.startswith("C:\\")
    assert state["calls"] == 2


def test_parse_disk_numbers_from_payload_uses_aligned_offset() -> None:
    if not hasattr(storage, "_parse_disk_numbers_from_volume_extents_payload"):
        pytest.skip("Windows disk parser is unavailable on this platform")

    extent_size = 24
    extents_offset = 8
    payload = bytearray(extents_offset + (extent_size * 2))
    payload[0:4] = (2).to_bytes(4, "little")
    payload[4:8] = (999).to_bytes(4, "little")
    payload[8:12] = (7).to_bytes(4, "little")
    payload[32:36] = (42).to_bytes(4, "little")

    disks = storage._parse_disk_numbers_from_volume_extents_payload(
        bytes(payload),
        2,
        extent_size=extent_size,
        extents_offset=extents_offset,
    )

    assert disks == {7, 42}


def test_list_windows_storage_roots_dedups_and_normalizes(monkeypatch) -> None:
    monkeypatch.setattr(storage.os, "name", "nt", raising=False)
    monkeypatch.setattr(storage, "list_logical_drive_roots", lambda: [Path("C:\\"), Path("D:\\")])
    monkeypatch.setattr(
        storage,
        "list_mounted_volume_paths",
        lambda: [Path("C:\\"), Path("C:\\mount\\disk1"), Path("C:\\mount\\disk1")],
    )
    monkeypatch.setattr(
        storage,
        "get_volume_mount_point",
        lambda path: Path(str(path).rstrip("\\")) if "mount" in str(path).lower() else Path(str(path)),
    )
    monkeypatch.setattr(storage.os.path, "isdir", lambda _path: True)

    roots = storage.list_windows_storage_roots()

    assert roots == [Path("C:\\"), Path("D:\\"), Path("C:\\mount\\disk1")]


def test_list_windows_storage_usage_returns_raw_values(monkeypatch) -> None:
    roots = [Path("C:\\"), Path("C:\\mount\\media01")]
    monkeypatch.setattr(storage.os, "name", "nt", raising=False)
    monkeypatch.setattr(storage, "list_windows_storage_roots", lambda: roots)
    monkeypatch.setattr(
        storage,
        "resolve_volume_identity",
        lambda path: f"volume:{path_key(path)}",
    )
    monkeypatch.setattr(
        storage,
        "resolve_physical_disk_tokens",
        lambda path: {"disk:0"} if str(path) == str(roots[0]) else {"disk:1", "disk:2"},
    )
    monkeypatch.setattr(
        storage,
        "_volume_label_for_root",
        lambda path: "System" if str(path) == str(roots[0]) else "Media",
    )
    monkeypatch.setattr(
        storage.shutil,
        "disk_usage",
        lambda path: SimpleNamespace(total=1000, free=400)
        if str(path) == str(roots[0])
        else SimpleNamespace(total=2000, free=500),
    )

    entries = storage.list_windows_storage_usage()

    assert entries[0] == storage.WindowsStorageUsage(
        root_path=Path("C:\\"),
        volume_identity="volume:c:\\",
        volume_label="System",
        disk_tokens={"disk:0"},
        bytes_used=600,
        bytes_total=1000,
    )
    assert entries[1] == storage.WindowsStorageUsage(
        root_path=Path("C:\\mount\\media01"),
        volume_identity=r"volume:c:\mount\media01",
        volume_label="Media",
        disk_tokens={"disk:1", "disk:2"},
        bytes_used=1500,
        bytes_total=2000,
    )


def test_list_windows_storage_usage_falls_back_to_volume_identity_and_empty_label(monkeypatch) -> None:
    root = Path("E:\\")
    monkeypatch.setattr(storage.os, "name", "nt", raising=False)
    monkeypatch.setattr(storage, "list_windows_storage_roots", lambda: [root])
    monkeypatch.setattr(storage, "resolve_volume_identity", lambda _path: "volume:e")

    def _raise_tokens(_path: Path) -> set[str]:
        raise OSError("no mapping")

    def _raise_label(_path: Path) -> str:
        raise OSError("no label")

    monkeypatch.setattr(storage, "resolve_physical_disk_tokens", _raise_tokens)
    monkeypatch.setattr(storage, "_volume_label_for_root", _raise_label)
    monkeypatch.setattr(
        storage.shutil,
        "disk_usage",
        lambda _path: SimpleNamespace(total=200, free=100),
    )

    entries = storage.list_windows_storage_usage()

    assert entries == [
        storage.WindowsStorageUsage(
            root_path=root,
            volume_identity="volume:e",
            volume_label="",
            disk_tokens={"volume:e"},
            bytes_used=100,
            bytes_total=200,
        )
    ]
