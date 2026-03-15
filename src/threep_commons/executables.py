"""Executable discovery helpers for Windows-first desktop tooling."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from .fs_paths import is_explicit_path_text, normalize_windows_path_text, path_key

if TYPE_CHECKING:
    from collections.abc import Sequence


def resolve_executable_path(raw: str) -> Path | None:
    """Resolve one explicit path or command name to an executable.

    Args:
        raw: Raw command text or filesystem path supplied by the caller.

    Returns:
        A resolved executable path when the target exists, otherwise ``None``.
    """
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
    """Return the first executable that resolves from the provided candidates.

    Args:
        preferred: Preferred executable path or command text to try first.
        command_names: Command names to resolve via ``PATH`` lookup.
        candidate_paths: Explicit candidate paths to probe in order.

    Returns:
        The first resolved executable path, or ``None`` when none are available.
    """
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
    """Build unique Program Files candidate paths for one relative executable path.

    Args:
        relative_path: Relative path appended beneath common Program Files roots.

    Returns:
        Candidate absolute paths in the order they should be tested.
    """
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
    for env_name in ("ProgramFiles", "ProgramFiles(x86)"):
        text = normalize_windows_path_text(os.environ.get(env_name, ""))
        if text and text not in roots:
            roots.append(text)
    return roots
