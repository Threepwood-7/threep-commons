"""Tests for Qt slot helpers."""

from __future__ import annotations

from typing import Any

from threep_commons.qt import safe_slot


class DummyWidget:
    """Simple object exposing a `log` method for safe-slot tests."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def log(self, message: str) -> None:
        self.messages.append(message)

    @safe_slot
    def explode(self) -> Any:
        raise RuntimeError("boom")


def test_safe_slot_logs_and_swallows_exception() -> None:
    widget = DummyWidget()

    result = widget.explode()

    assert result is None
    assert widget.messages
