"""Shared subprocess kwargs helpers."""

from __future__ import annotations

import logging
import subprocess
import sys
from typing import Any

LOGGER = logging.getLogger(__name__)


def _windows_no_window_kwargs() -> dict[str, object]:
    """Build subprocess kwargs that suppress transient Windows console windows."""
    if sys.platform != "win32":
        return {}

    kwargs: dict[str, object] = {}
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
        kwargs["startupinfo"] = startupinfo
    except Exception as exc:
        LOGGER.debug(
            "Unable to configure Windows STARTUPINFO console suppression.",
            exc_info=exc,
        )

    creationflags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if creationflags:
        kwargs["creationflags"] = creationflags
    return kwargs


def windows_no_window_popen_kwargs() -> dict[str, object]:
    """Return subprocess kwargs that hide Windows console popups for Popen."""

    return _windows_no_window_kwargs()


def windows_no_window_run_kwargs() -> dict[str, object]:
    """Return subprocess kwargs that hide Windows console popups for run."""

    return _windows_no_window_kwargs()


def merge_subprocess_kwargs(*parts: dict[str, Any]) -> dict[str, Any]:
    """Merge subprocess kwargs dictionaries from left to right."""

    merged: dict[str, Any] = {}
    for part in parts:
        merged.update(dict(part))
    return merged
