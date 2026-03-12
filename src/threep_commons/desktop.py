"""Desktop launch helpers for opening and revealing local paths."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _coerce_path_text(path: str | Path) -> str:
    return str(path or "").strip()


def _path_for_launch(path: str | Path) -> Path:
    return Path(_coerce_path_text(path)).expanduser()


def open_path_in_default_app(path: str | Path) -> bool:
    """Open one local file, directory, or URL in the platform default app."""

    text = _coerce_path_text(path)
    if not text:
        return False

    try:
        if sys.platform == "win32":
            os.startfile(text)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", text])
        else:
            subprocess.Popen(["xdg-open", text])
        return True
    except (AttributeError, OSError, subprocess.SubprocessError):
        return False


def open_parent_directory(path: str | Path) -> bool:
    """Open the containing directory for one target path."""

    text = _coerce_path_text(path)
    if not text:
        return False
    target = _path_for_launch(text)
    parent = target if target.is_dir() else target.parent
    return open_path_in_default_app(parent)


def reveal_path_in_file_manager(path: str | Path) -> bool:
    """Reveal one path in the platform file manager."""

    text = _coerce_path_text(path)
    if not text:
        return False
    target = _path_for_launch(text)

    try:
        if sys.platform == "win32":
            if target.exists() and target.is_dir():
                subprocess.Popen(["explorer", str(target)])
            else:
                subprocess.Popen(["explorer", f"/select,{target}"])
            return True
        if sys.platform == "darwin":
            if target.exists() and target.is_file():
                subprocess.Popen(["open", "-R", str(target)])
            else:
                subprocess.Popen(
                    ["open", str(target if target.is_dir() else target.parent)]
                )
            return True
        parent = target if target.is_dir() else target.parent
        subprocess.Popen(["xdg-open", str(parent)])
        return True
    except (OSError, subprocess.SubprocessError):
        return False
