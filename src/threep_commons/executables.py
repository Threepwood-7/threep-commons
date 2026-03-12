from __future__ import annotations

import os
import shutil
from collections.abc import Sequence
from pathlib import Path

from .fs_paths import is_explicit_path_text, normalize_windows_path_text, path_key


def resolve_executable_path(raw: str) -> Path | None:
    text = normalize_windows_path_text(str(raw or "").strip())
    if not text:
        return None
    if is_explicit_path_text(text):
        candidate = Path(text)
        if candidate.exists():
            return candidate
        return None
    which_hit = shutil.which(text)
    if which_hit:
        return Path(normalize_windows_path_text(which_hit))
    return None


def find_first_available_executable(
    *,
    preferred: str | Path | None = None,
    command_names: Sequence[str] = (),
    candidate_paths: Sequence[str | Path] = (),
) -> Path | None:
    if preferred is not None:
        resolved = resolve_executable_path(str(preferred))
        if resolved is not None:
            return resolved

    for command_name in command_names:
        resolved = resolve_executable_path(str(command_name))
        if resolved is not None:
            return resolved

    for candidate_path in candidate_paths:
        resolved = resolve_executable_path(str(candidate_path))
        if resolved is not None:
            return resolved
    return None


def program_files_candidates(relative_path: str | Path) -> list[Path]:
    rel_text = normalize_windows_path_text(str(relative_path or "").strip())
    if not rel_text:
        return []
    relative = Path(rel_text)
    candidates: list[Path] = []
    seen: set[str] = set()
    for base_text in _program_files_roots():
        candidate = Path(base_text) / relative
        key = path_key(candidate)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(candidate)
    return candidates


def _program_files_roots() -> list[str]:
    roots: list[str] = []
    for env_name, fallback in (
        ("ProgramFiles", r"C:\Program Files"),
        ("ProgramFiles(x86)", r"C:\Program Files (x86)"),
    ):
        text = normalize_windows_path_text(os.environ.get(env_name, "") or fallback)
        if text and text not in roots:
            roots.append(text)
    return roots
