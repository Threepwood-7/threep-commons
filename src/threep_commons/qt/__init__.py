"""Qt-specific helpers shared across PySide-based apps."""

from .slots import safe_slot
from .widget_identity import (
    assign_widget_identity,
    normalize_widget_id,
    object_name_for_id,
)

__all__ = [
    "assign_widget_identity",
    "normalize_widget_id",
    "object_name_for_id",
    "safe_slot",
]
