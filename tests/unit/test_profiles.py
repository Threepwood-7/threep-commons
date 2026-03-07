"""Tests for shared profile persistence helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from threep_commons import AppIdentity
from threep_commons.profiles import (
    delete_profile_config,
    list_profile_ids,
    load_profile_config_with_issues,
    normalize_profile_id,
    profile_store_file_path,
    save_profile_config,
)

if TYPE_CHECKING:
    from pathlib import Path

SCHEMA = (
    ("host", str, "127.0.0.1"),
    ("port", int, 8080),
    ("password", str, ""),
)
DEFAULTS = {"host": "127.0.0.1", "port": 8080, "password": ""}


def test_profile_roundtrip(tmp_path: Path, monkeypatch) -> None:
    identity = AppIdentity("ThreepSoftwz", "demo_app", "Demo App")
    monkeypatch.setenv("DEMO_PASSWORD", "secret")

    normalized = save_profile_config(
        identity,
        "Main Profile",
        {"host": "example.local", "port": 9091},
        SCHEMA,
        DEFAULTS,
        config_dir_override=tmp_path / "cfg",
    )
    loaded, issues = load_profile_config_with_issues(
        identity,
        normalized,
        SCHEMA,
        DEFAULTS,
        secret_env_to_keys=(("DEMO_PASSWORD", ("password",)),),
        config_dir_override=tmp_path / "cfg",
    )

    assert issues == []
    assert normalized == "main-profile"
    assert loaded["host"] == "example.local"
    assert loaded["port"] == 9091
    assert loaded["password"] == "secret"
    assert (
        list_profile_ids(identity, config_dir_override=tmp_path / "cfg")[0] == "default"
    )
    assert profile_store_file_path(
        identity, config_dir_override=tmp_path / "cfg"
    ).endswith("demo_app.ini")


def test_missing_profile_is_seeded(tmp_path: Path) -> None:
    identity = AppIdentity("ThreepSoftwz", "demo_app", "Demo App")

    loaded, issues = load_profile_config_with_issues(
        identity,
        None,
        SCHEMA,
        DEFAULTS,
        config_dir_override=tmp_path / "cfg",
    )

    assert issues
    assert loaded["_profile_id"] == "default"
    assert normalize_profile_id(" Main Profile ") == "main-profile"

    delete_profile_config(identity, "default", config_dir_override=tmp_path / "cfg")
