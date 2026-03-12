"""Tests for shared widget identity helpers."""

from __future__ import annotations

from threep_commons.qt.widget_identity import (
    assign_widget_identity,
    normalize_widget_id,
    object_name_for_id,
)


class _FakeWidget:
    def __init__(self) -> None:
        self.object_name = ""
        self.properties: dict[str, str] = {}

    def setObjectName(self, value: str) -> None:  # noqa: N802
        self.object_name = value

    def setProperty(self, key: str, value: str) -> None:  # noqa: N802
        self.properties[key] = value


def test_normalize_widget_id_trims_whitespace() -> None:
    assert normalize_widget_id("  window:main  ") == "window:main"


def test_object_name_for_id_sanitizes_qt_identifier() -> None:
    assert (
        object_name_for_id("window:main:control:url_input")
        == "window_main_control_url_input"
    )


def test_assign_widget_identity_sets_object_name_and_properties() -> None:
    widget = _FakeWidget()

    assign_widget_identity(
        widget,
        widget_id="window:main:control:capture_button",
        widget_alias="capture_button",
    )

    assert widget.object_name == "window_main_control_capture_button"
    assert widget.properties["widget_id"] == "window:main:control:capture_button"
    assert widget.properties["widget_alias"] == "capture_button"
