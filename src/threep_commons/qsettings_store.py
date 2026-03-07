"""Thin QSettings store helpers shared across apps."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QSettings

from .config_helpers import SchemaEntry, coerce_value
from .paths import configure_qsettings

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from .app_identity import AppIdentity


def create_qsettings(
    identity: AppIdentity,
    *,
    app_name: str | None = None,
    config_dir_override: str | Path | None = None,
) -> QSettings:
    """Create one QSettings object using the configured shared INI root."""

    configure_qsettings(identity, config_dir_override)
    return QSettings(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
        identity.org_name,
        app_name or identity.app_name,
    )


def qsettings_store_file_path(
    identity: AppIdentity,
    *,
    app_name: str | None = None,
    config_dir_override: str | Path | None = None,
) -> str:
    """Return the current QSettings store file path."""

    settings = create_qsettings(
        identity,
        app_name=app_name,
        config_dir_override=config_dir_override,
    )
    settings.sync()
    return str(settings.fileName() or "").strip()


def ensure_schema_defaults(settings: QSettings, schema: Sequence[SchemaEntry]) -> bool:
    """Seed missing schema keys into one QSettings store."""

    changed = False
    for key, expected_type, default in schema:
        if settings.contains(key):
            continue
        settings.setValue(key, coerce_value(default, expected_type, default))
        changed = True
    if changed:
        settings.sync()
    return changed
