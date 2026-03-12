"""Schema-driven profile persistence helpers backed by the shared settings store."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from .config_helpers import (
    EnvKeyMapping,
    SchemaEntry,
    apply_env_overrides,
    coerce_value,
)
from .qsettings_store import qsettings_store_file_path
from .settings import QSettingsValueStore

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from .app_identity import AppIdentity


def normalize_profile_id(value: object, default_profile_id: str = "default") -> str:
    """Normalize one free-form profile identifier to a safe token."""

    raw = str(value or "").strip().lower()
    if not raw:
        return default_profile_id
    cleaned = re.sub(r"[^a-z0-9_-]+", "-", raw).strip("-_")
    return cleaned or default_profile_id


def _profile_base_key(
    profile_root: str, profile_id: str, default_profile_id: str
) -> str:
    return f"{profile_root}/{normalize_profile_id(profile_id, default_profile_id)}"


def list_profile_ids(
    identity: AppIdentity,
    *,
    profile_root: str = "profiles",
    default_profile_id: str = "default",
    config_dir_override: str | Path | None = None,
) -> list[str]:
    """List normalized profile identifiers stored in the settings store."""

    store = QSettingsValueStore.from_identity(
        identity,
        config_dir_override=config_dir_override,
    )
    profiles = [
        normalize_profile_id(group, default_profile_id)
        for group in store.child_groups(profile_root)
    ]
    deduped = sorted({profile for profile in profiles if profile})
    if default_profile_id not in deduped:
        deduped.insert(0, default_profile_id)
    return deduped


def profile_store_file_path(
    identity: AppIdentity,
    *,
    config_dir_override: str | Path | None = None,
) -> str:
    """Return the QSettings storage file backing the profile store."""

    return qsettings_store_file_path(identity, config_dir_override=config_dir_override)


def save_profile_config(
    identity: AppIdentity,
    profile_id: str,
    config: Mapping[str, Any],
    schema: Sequence[SchemaEntry],
    defaults: Mapping[str, Any],
    *,
    profile_root: str = "profiles",
    default_profile_id: str = "default",
    config_dir_override: str | Path | None = None,
) -> str:
    """Persist one profile into QSettings and return the normalized id."""

    normalized_profile = normalize_profile_id(profile_id, default_profile_id)
    merged = dict(defaults)
    merged.update(dict(config))

    base_key = _profile_base_key(profile_root, normalized_profile, default_profile_id)
    store = QSettingsValueStore.from_identity(
        identity,
        config_dir_override=config_dir_override,
        namespace=base_key,
    )
    for key, expected_type, default in schema:
        store.set_value(
            key,
            coerce_value(merged.get(key, default), expected_type, default),
        )
    store.sync()
    return normalized_profile


def delete_profile_config(
    identity: AppIdentity,
    profile_id: str,
    *,
    profile_root: str = "profiles",
    default_profile_id: str = "default",
    config_dir_override: str | Path | None = None,
) -> None:
    """Delete one named profile from the settings store."""

    normalized_profile = normalize_profile_id(profile_id, default_profile_id)
    store = QSettingsValueStore.from_identity(
        identity,
        config_dir_override=config_dir_override,
    )
    store.remove(
        _profile_base_key(profile_root, normalized_profile, default_profile_id)
    )
    store.sync()


def load_profile_config_with_issues(
    identity: AppIdentity,
    profile_id: str | None,
    schema: Sequence[SchemaEntry],
    defaults: Mapping[str, Any],
    *,
    profile_root: str = "profiles",
    default_profile_id: str = "default",
    normalized_profile_key: str = "_profile_id",
    secret_env_to_keys: EnvKeyMapping = (),
    config_dir_override: str | Path | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Load one profile-backed config mapping and collect non-fatal issues."""

    issues: list[str] = []
    normalized_profile = normalize_profile_id(profile_id, default_profile_id)
    base_key = _profile_base_key(profile_root, normalized_profile, default_profile_id)
    root_store = QSettingsValueStore.from_identity(
        identity,
        config_dir_override=config_dir_override,
    )
    profile_store = QSettingsValueStore.from_identity(
        identity,
        config_dir_override=config_dir_override,
        namespace=base_key,
    )

    profile_exists = any(
        root_store.contains(f"{base_key}/{key}") for key, _type, _default in schema
    )
    if not profile_exists:
        issues.append(
            f"Profile '{normalized_profile}' not found in QSettings; seeding defaults."
        )
        save_profile_config(
            identity,
            normalized_profile,
            defaults,
            schema,
            defaults,
            profile_root=profile_root,
            default_profile_id=default_profile_id,
            config_dir_override=config_dir_override,
        )

    loaded: dict[str, Any] = dict(defaults)
    for key, expected_type, default in schema:
        raw = profile_store.value(key, default)
        loaded[key] = coerce_value(raw, expected_type, default)
    loaded[normalized_profile_key] = normalized_profile
    apply_env_overrides(loaded, secret_env_to_keys)
    return loaded, issues


def load_profile_config(
    identity: AppIdentity,
    profile_id: str | None,
    schema: Sequence[SchemaEntry],
    defaults: Mapping[str, Any],
    *,
    profile_root: str = "profiles",
    default_profile_id: str = "default",
    normalized_profile_key: str = "_profile_id",
    secret_env_to_keys: EnvKeyMapping = (),
    config_dir_override: str | Path | None = None,
) -> dict[str, Any]:
    """Load one profile-backed config mapping without returning the issue list."""

    config, _issues = load_profile_config_with_issues(
        identity,
        profile_id,
        schema,
        defaults,
        profile_root=profile_root,
        default_profile_id=default_profile_id,
        normalized_profile_key=normalized_profile_key,
        secret_env_to_keys=secret_env_to_keys,
        config_dir_override=config_dir_override,
    )
    return config
