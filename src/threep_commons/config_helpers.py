"""Shared coercion, merge, and nested-mapping helpers."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import Any, cast

type SchemaEntry = tuple[str, type[Any], Any]
type EnvKeyMapping = Sequence[tuple[str, Sequence[str]]]


def set_nested_value(
    target: dict[str, Any], key_path: Sequence[str], value: Any
) -> None:
    """Set a value below one nested key path, creating dict nodes as needed."""

    current: dict[str, Any] = target
    for key in key_path[:-1]:
        next_value = current.get(key)
        if not isinstance(next_value, dict):
            next_value = {}
            current[key] = next_value
        current = cast("dict[str, Any]", next_value)
    current[key_path[-1]] = value


def schema_key_path(
    schema_key: str, prefix_to_strip: str | None = "config"
) -> tuple[str, ...]:
    """Convert one slash-delimited schema key into a nested mapping path."""

    parts = tuple(part for part in schema_key.split("/") if part)
    if prefix_to_strip and parts and parts[0] == prefix_to_strip:
        return parts[1:]
    return parts


def deep_merge_dicts(
    base: Mapping[str, Any], overlay: Mapping[str, Any]
) -> dict[str, Any]:
    """Deep-merge two mappings and return a new dictionary."""

    merged: dict[str, Any] = dict(base)
    for key, value in overlay.items():
        base_value = merged.get(key)
        if isinstance(base_value, Mapping) and isinstance(value, Mapping):
            merged[key] = deep_merge_dicts(
                cast("Mapping[str, Any]", base_value),
                cast("Mapping[str, Any]", value),
            )
        else:
            merged[key] = value
    return merged


def coerce_bool(value: Any, default: bool) -> bool:
    """Coerce one runtime value into a bool with a fallback default."""

    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        token = value.strip().lower()
        if token in {"1", "true", "yes", "on"}:
            return True
        if token in {"0", "false", "no", "off"}:
            return False
    return bool(default)


def coerce_value(value: Any, expected_type: type[Any], default: Any) -> Any:
    """Coerce one runtime value into the requested scalar type."""

    if expected_type is bool:
        return coerce_bool(value, bool(default))
    if expected_type is int:
        try:
            return int(value)
        except (TypeError, ValueError, OverflowError):
            return int(default)
    if expected_type is float:
        try:
            return float(value)
        except (TypeError, ValueError, OverflowError):
            return float(default)
    if value is None:
        return default
    return str(value)


def value_at_path(source: Mapping[str, Any], path: Sequence[str], default: Any) -> Any:
    """Read one nested mapping path and fall back when any node is missing."""

    current: object = source
    for key in path:
        if not isinstance(current, Mapping):
            return default
        current = current.get(key, default)
    return current


def apply_env_overrides(target: dict[str, Any], env_to_keys: EnvKeyMapping) -> None:
    """Apply environment-variable overrides into one nested mapping."""

    for env_name, key_path in env_to_keys:
        env_value = os.environ.get(env_name, "")
        if env_value:
            set_nested_value(target, key_path, env_value)
