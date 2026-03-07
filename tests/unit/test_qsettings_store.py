"""Tests for QSettings store helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from threep_commons import AppIdentity
from threep_commons.qsettings_store import (
    create_qsettings,
    ensure_schema_defaults,
    qsettings_store_file_path,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_create_qsettings_and_store_file_path(tmp_path: Path) -> None:
    identity = AppIdentity("ThreepSoftwz", "demo_app", "Demo App")

    settings = create_qsettings(identity, config_dir_override=tmp_path / "cfg")
    settings.setValue("demo/value", 7)
    settings.sync()

    store_path = qsettings_store_file_path(
        identity, config_dir_override=tmp_path / "cfg"
    )

    assert store_path
    assert store_path.endswith("demo_app.ini")


def test_ensure_schema_defaults(tmp_path: Path) -> None:
    identity = AppIdentity("ThreepSoftwz", "demo_app", "Demo App")
    settings = create_qsettings(identity, config_dir_override=tmp_path / "cfg")

    changed = ensure_schema_defaults(
        settings,
        (
            ("demo/enabled", bool, True),
            ("demo/count", int, 3),
        ),
    )

    assert changed is True
    assert settings.value("demo/enabled") is True
    assert settings.value("demo/count") == 3
