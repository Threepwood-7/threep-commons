"""Tests for shared config helpers."""

from __future__ import annotations

from threep_commons.config_helpers import (
    apply_env_overrides,
    coerce_bool,
    coerce_value,
    deep_merge_dicts,
    schema_key_path,
    set_nested_value,
    value_at_path,
)


def test_set_nested_value_and_value_at_path() -> None:
    target: dict[str, object] = {}
    set_nested_value(target, ("alpha", "beta"), 42)

    assert target == {"alpha": {"beta": 42}}
    assert value_at_path(target, ("alpha", "beta"), None) == 42


def test_deep_merge_dicts() -> None:
    merged = deep_merge_dicts(
        {"alpha": {"beta": 1, "gamma": 2}},
        {"alpha": {"gamma": 3}, "delta": 4},
    )

    assert merged == {"alpha": {"beta": 1, "gamma": 3}, "delta": 4}


def test_coerce_helpers(monkeypatch) -> None:
    monkeypatch.setenv("DEMO_TOKEN", "secret")
    target = {"demo": {"token": ""}}

    apply_env_overrides(target, (("DEMO_TOKEN", ("demo", "token")),))

    assert coerce_bool("yes", False) is True
    assert coerce_value("42", int, 0) == 42
    assert coerce_value("3.5", float, 0.0) == 3.5
    assert coerce_value(None, str, "fallback") == "fallback"
    assert schema_key_path("config/demo/token") == ("demo", "token")
    assert target["demo"] == {"token": "secret"}
