"""Deterministic Qt widget identity helpers shared across apps."""

from __future__ import annotations

import re

_OBJECT_NAME_RE = re.compile(r"[^A-Za-z0-9_]+")


def normalize_widget_id(widget_id: str) -> str:
    """Normalize one widget id to the canonical trimmed text form."""

    return str(widget_id or "").strip()


def object_name_for_id(widget_id: str) -> str:
    """Convert one widget id into a Qt-safe object name."""

    normalized = _OBJECT_NAME_RE.sub("_", normalize_widget_id(widget_id)).strip("_")
    if not normalized:
        return "widget"
    if normalized[0].isdigit():
        return f"w_{normalized}"
    return normalized


def assign_widget_identity(
    widget: object, *, widget_id: str, widget_alias: str
) -> None:
    """Assign stable identity properties to one Qt widget."""

    widget_id_text = normalize_widget_id(widget_id)
    alias_text = str(widget_alias or "").strip()
    widget.setObjectName(object_name_for_id(widget_id_text))
    widget.setProperty("widget_id", widget_id_text)
    widget.setProperty("widget_alias", alias_text)
