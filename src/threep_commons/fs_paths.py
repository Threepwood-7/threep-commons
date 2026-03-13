"""Cross-platform path normalization helpers with Windows-aware semantics."""

from __future__ import annotations

import os
import re
from pathlib import Path, PureWindowsPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

WINDOWS_DRIVE_PATH_RE = re.compile(r"^[A-Za-z]:[\\/]")
WINDOWS_UNC_PATH_RE = re.compile(r"^[\\/]{2}[^\\/]+[\\/][^\\/]+")
WINDOWS_DEVICE_PATH_RE = re.compile(r"^[\\/]{2}[?.][\\/]")


def coerce_path(value: Path | str) -> Path:
    """Normalize one raw path-like value into a ``Path`` instance.

    Args:
        value: Raw string or ``Path`` value supplied by the caller.

    Returns:
        A normalized ``Path`` with user-home expansion applied.
    """
    if isinstance(value, Path):
        return value.expanduser()
    return Path(normalize_windows_path_text(str(value))).expanduser()


def normalize_windows_path_text(raw: str) -> str:
    """Normalize Windows-looking path text without forcing non-path strings.

    Args:
        raw: Raw path text or command text to normalize.

    Returns:
        Normalized path text when the input looks path-like, otherwise the
        stripped original text.
    """
    text = str(raw or "").strip()
    if not text:
        return text
    if not _looks_like_windows_path(text) and not _has_path_separator(text):
        return text
    return str(PureWindowsPath(text))


def strip_windows_long_path_text(text: str) -> str:
    """Remove Windows long-path prefixes from path text when present.

    Args:
        text: Path text that may include a ``\\\\?\\`` prefix.

    Returns:
        Display-friendly Windows path text.
    """
    raw = normalize_windows_path_text(str(text or ""))
    if raw.startswith("\\\\?\\UNC\\"):
        return normalize_windows_path_text(f"\\\\{raw[8:]}")
    if raw.startswith("\\\\?\\"):
        return normalize_windows_path_text(raw[4:])
    return raw


def display_path_text(path: Path | str) -> str:
    """Return path text suitable for logs, UI, and stable comparisons.

    Args:
        path: Raw path value to render.

    Returns:
        A display-safe path string with Windows long-path prefixes removed.
    """
    raw = str(path)
    if not raw:
        return raw
    if _is_windows() or raw.startswith("\\\\?\\") or _looks_like_windows_path(raw):
        return strip_windows_long_path_text(raw)
    return raw


def path_key(path: Path | str) -> str:
    """Build a normalized comparison key for one path.

    Args:
        path: Path value to normalize for case-insensitive comparisons.

    Returns:
        A normalized string key suitable for deduplication and lookups.
    """
    normalized = display_path_text(coerce_path(path))
    if _is_windows() or _looks_like_windows_path(normalized):
        return normalize_windows_path_text(normalized).casefold()
    return str(Path(normalized))


def is_drive_root(path: Path | str) -> bool:
    """Return whether the provided path resolves to a drive root.

    Args:
        path: Path value to inspect.

    Returns:
        ``True`` when the path is exactly a drive root, otherwise ``False``.
    """
    candidate = coerce_path(path)
    if not candidate.drive:
        return False
    return path_key(candidate) == path_key(Path(f"{candidate.drive}{os.sep}"))


def is_path_under_root(path: Path | str, root: Path | str) -> bool:
    """Return whether a path is equal to or nested beneath a root path.

    Args:
        path: Candidate path to check.
        root: Root path that should contain the candidate.

    Returns:
        ``True`` when the candidate is the root or one of its descendants.
    """
    candidate_key = path_key(path)
    root_key = path_key(root)
    if candidate_key == root_key:
        return True
    separator = "\\" if _uses_windows_path_semantics(root, path) else os.sep
    prefix = root_key if root_key.endswith(separator) else f"{root_key}{separator}"
    return candidate_key.startswith(prefix)


def display_root(path: Path | str) -> str:
    """Return a compact display label for a root path.

    Args:
        path: Root-like path value to render.

    Returns:
        The drive letter for drive roots, otherwise normalized display text.
    """
    candidate = coerce_path(path)
    if is_drive_root(candidate):
        return candidate.drive
    return display_path_text(candidate)


def dedup_paths(paths: Iterable[Path | str], *, require_existing: bool) -> list[Path]:
    """Deduplicate path values while preserving order.

    Args:
        paths: Candidate path values to normalize and deduplicate.
        require_existing: Whether to drop values that do not exist as folders.

    Returns:
        Unique normalized paths in first-seen order.
    """
    deduped: list[Path] = []
    seen: set[str] = set()
    for raw_path in paths:
        candidate = coerce_path(raw_path)
        if require_existing and (not candidate.exists() or not candidate.is_dir()):
            continue
        key = path_key(candidate)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def is_explicit_path_text(raw: str) -> bool:
    """Return whether raw text looks like an explicit filesystem path.

    Args:
        raw: Raw text to classify.

    Returns:
        ``True`` when the text is absolute or contains path separators.
    """
    text = normalize_windows_path_text(str(raw or "").strip())
    if not text:
        return False
    candidate = Path(text)
    return candidate.is_absolute() or _has_path_separator(text)


def _is_windows() -> bool:
    return os.name == "nt"


def _looks_like_windows_path(text: str) -> bool:
    return bool(
        WINDOWS_DRIVE_PATH_RE.match(text)
        or WINDOWS_UNC_PATH_RE.match(text)
        or WINDOWS_DEVICE_PATH_RE.match(text)
    )


def _has_path_separator(text: str) -> bool:
    return "\\" in text or "/" in text


def _uses_windows_path_semantics(*paths: Path | str) -> bool:
    if _is_windows():
        return True
    return any(_looks_like_windows_path(str(path)) for path in paths)
