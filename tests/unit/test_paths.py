"""Tests for shared path helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from threep_commons import AppIdentity
from threep_commons.paths import (
    configure_qsettings,
    resolve_app_data_dir,
    resolve_config_root,
    resolve_data_root,
    resolve_log_dir,
    resolve_settings_dir,
    resolve_settings_file,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_resolve_paths_from_explicit_overrides(tmp_path: Path) -> None:
    identity = AppIdentity("ThreepSoftwz", "demo_app", "Demo App")
    config_root = resolve_config_root(tmp_path / "cfg")
    data_root = resolve_data_root(identity, tmp_path / "data")
    app_dir = resolve_app_data_dir(identity, tmp_path / "data")
    log_dir = resolve_log_dir(identity, tmp_path / "data")
    settings_dir = resolve_settings_dir(identity, tmp_path / "cfg")
    settings_file = resolve_settings_file(identity, tmp_path / "cfg")

    assert config_root == (tmp_path / "cfg").resolve()
    assert data_root == (tmp_path / "data").resolve()
    assert app_dir == (tmp_path / "data" / "demo_app").resolve()
    assert log_dir == (tmp_path / "data" / "demo_app" / "logs").resolve()
    assert settings_dir == (tmp_path / "cfg" / "ThreepSoftwz").resolve()
    assert (
        settings_file == (tmp_path / "cfg" / "ThreepSoftwz" / "demo_app.ini").resolve()
    )


def test_configure_qsettings_returns_root(tmp_path: Path) -> None:
    identity = AppIdentity("ThreepSoftwz", "demo_app", "Demo App")

    configured_root = configure_qsettings(identity, tmp_path / "cfg")

    assert configured_root == (tmp_path / "cfg").resolve()
