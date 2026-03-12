"""Tests for shared subprocess helper kwargs."""

from __future__ import annotations

from threep_commons.subprocess_helpers import (
    merge_subprocess_kwargs,
    windows_no_window_run_kwargs,
)


def test_windows_no_window_run_kwargs_include_creationflags_on_windows(monkeypatch) -> None:
    monkeypatch.setattr("threep_commons.subprocess_helpers.sys.platform", "win32")
    monkeypatch.setattr(
        "threep_commons.subprocess_helpers.subprocess.CREATE_NO_WINDOW",
        0x08000000,
        raising=False,
    )

    kwargs = windows_no_window_run_kwargs()

    assert kwargs["creationflags"] == 0x08000000


def test_merge_subprocess_kwargs_prefers_later_values() -> None:
    merged = merge_subprocess_kwargs({"creationflags": 1}, {"check": False}, {"creationflags": 2})
    assert merged == {"creationflags": 2, "check": False}
