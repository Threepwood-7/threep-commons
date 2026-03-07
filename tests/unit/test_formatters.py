"""Tests for shared formatters."""

from threep_commons.formatters import (
    format_age,
    format_datetime,
    format_eta,
    format_float,
    format_int,
    format_size,
    format_size_mode,
    format_speed_mode,
)


def test_scalar_formatters() -> None:
    assert format_float(1.234) == "1.23"
    assert format_int(1234) == "1,234"
    assert format_datetime(0) == ""


def test_size_and_speed_formatters() -> None:
    assert format_size(0) == "0 B"
    assert format_size_mode(2048) == "2.00 KB"
    assert format_size_mode(2048, mode="bytes") == "2,048"
    assert format_speed_mode(2048) == "2.00 KB/s"


def test_eta_and_age_formatters() -> None:
    assert format_eta(3661) == "1h 01m"
    assert format_age(0.5) == "<1d"
    assert format_age(5) == "5d"
