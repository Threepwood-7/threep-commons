from __future__ import annotations

from pathlib import Path

from threep_commons.executables import (
    find_first_available_executable,
    program_files_candidates,
    resolve_executable_path,
)


def test_resolve_executable_path_prefers_explicit_existing(tmp_path: Path) -> None:
    exe = tmp_path / "tool.exe"
    exe.write_text("", encoding="utf-8")

    assert resolve_executable_path(str(exe)) == exe


def test_resolve_executable_path_uses_path_lookup(monkeypatch) -> None:
    monkeypatch.setattr(
        "threep_commons.executables.shutil.which",
        lambda _name: r"C:\bin\tool.exe",
    )

    assert resolve_executable_path("tool") == Path(r"C:\bin\tool.exe")


def test_find_first_available_executable_checks_preferred_then_candidates(
    monkeypatch, tmp_path: Path
) -> None:
    preferred = tmp_path / "missing.exe"
    candidate = tmp_path / "found.exe"
    candidate.write_text("", encoding="utf-8")

    monkeypatch.setattr("threep_commons.executables.shutil.which", lambda _name: None)

    assert (
        find_first_available_executable(
            preferred=preferred,
            command_names=("tool",),
            candidate_paths=(candidate,),
        )
        == candidate
    )


def test_program_files_candidates_emits_standard_roots(monkeypatch) -> None:
    monkeypatch.setenv("ProgramFiles", r"C:\PF")
    monkeypatch.setenv("ProgramFiles(x86)", r"C:\PF86")

    candidates = program_files_candidates(Path("WinMerge") / "WinMergeU.exe")

    assert candidates == [
        Path(r"C:\PF\WinMerge\WinMergeU.exe"),
        Path(r"C:\PF86\WinMerge\WinMergeU.exe"),
    ]
