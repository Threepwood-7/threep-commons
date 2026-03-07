"""Shared formatting helpers for values displayed across apps."""

from __future__ import annotations

from datetime import datetime


def format_float(value: float, decimals: int = 2) -> str:
    """Format one float with the requested precision, or empty when zero."""

    if value != 0:
        return f"{value:.{decimals}f}"
    return ""


def format_int(value: int) -> str:
    """Format one integer with grouping, or empty when zero."""

    if value != 0:
        return f"{value:,}"
    return ""


def format_datetime(timestamp: int) -> str:
    """Format one UNIX timestamp as local time."""

    if timestamp > 0:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    return ""


def normalize_display_mode(value: object, default: str = "human_readable") -> str:
    """Normalize one display mode to `bytes` or `human_readable`."""

    mode = str(value or default).strip().lower()
    if mode in {"bytes", "human_readable"}:
        return mode
    return default


def format_size_mode(bytes_size: int, mode: str = "human_readable") -> str:
    """Format a byte count according to the selected display mode."""

    normalized_mode = normalize_display_mode(mode)
    size_value = int(bytes_size or 0)
    if normalized_mode == "bytes":
        return f"{size_value:,}"
    if size_value == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    size = float(size_value)
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    return f"{size:.2f} {units[unit_index]}"


def format_size(bytes_size: int) -> str:
    """Format one byte count using human-readable units."""

    return format_size_mode(bytes_size, mode="human_readable")


def format_speed_mode(bytes_per_sec: int, mode: str = "human_readable") -> str:
    """Format one byte-per-second rate according to the selected display mode."""

    speed_value = int(bytes_per_sec or 0)
    if speed_value == 0:
        return ""
    normalized_mode = normalize_display_mode(mode)
    if normalized_mode == "bytes":
        return f"{speed_value:,}"
    return f"{format_size_mode(speed_value, mode='human_readable')}/s"


def format_speed(bytes_per_sec: int) -> str:
    """Format one byte-per-second rate using human-readable units."""

    return format_speed_mode(bytes_per_sec, mode="human_readable")


def format_eta(seconds: int) -> str:
    """Format one ETA value into a compact human-readable string."""

    try:
        eta = int(seconds)
    except (TypeError, ValueError, OverflowError):
        return ""
    if eta <= 0:
        return ""

    days, remainder = divmod(eta, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    if days > 0:
        return f"{days}d {hours:02d}h"
    if hours > 0:
        return f"{hours}h {minutes:02d}m"
    if minutes > 0:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def format_age(days: float | int | None) -> str:
    """Format an age expressed in days."""

    if days is None:
        return ""
    if days < 1:
        return "<1d"
    if days < 365:
        return f"{int(days)}d"
    years = float(days) / 365.25
    return f"{years:.1f}y"
