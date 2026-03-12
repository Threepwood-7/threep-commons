"""Tests for shared desktop launch helpers."""

from __future__ import annotations

from pathlib import Path

from threep_commons.desktop import (
    open_parent_directory,
    open_path_in_default_app,
    reveal_path_in_file_manager,
)


def test_open_path_in_default_app_uses_windows_launcher(monkeypatch) -> None:
    opened: list[str] = []

    monkeypatch.setattr("threep_commons.desktop.sys.platform", "win32")
    monkeypatch.setattr(
        "threep_commons.desktop.os.startfile",
        lambda path: opened.append(path),
        raising=False,
    )

    assert open_path_in_default_app(r"C:\demo.txt") is True
    assert opened == [r"C:\demo.txt"]


def test_reveal_path_in_file_manager_selects_files_on_windows(
    monkeypatch, tmp_path: Path
) -> None:
    launched: list[list[str]] = []
    target = tmp_path / "demo.txt"
    target.write_text("demo", encoding="utf-8")

    monkeypatch.setattr("threep_commons.desktop.sys.platform", "win32")
    monkeypatch.setattr(
        "threep_commons.desktop.subprocess.Popen",
        lambda args: launched.append(list(args)),
    )

    assert reveal_path_in_file_manager(target) is True
    assert launched == [["explorer", f"/select,{target}"]]


def test_open_parent_directory_opens_containing_directory(
    monkeypatch, tmp_path: Path
) -> None:
    opened: list[Path] = []
    target = tmp_path / "folder" / "demo.txt"
    target.parent.mkdir(parents=True)
    target.write_text("demo", encoding="utf-8")

    monkeypatch.setattr(
        "threep_commons.desktop.open_path_in_default_app",
        lambda path: opened.append(Path(path)) or True,
    )

    assert open_parent_directory(target) is True
    assert opened == [target.parent]
