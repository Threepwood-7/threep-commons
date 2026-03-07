"""Filesystem and QSettings path helpers built around :class:`AppIdentity`."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QSettings

if TYPE_CHECKING:
    from .app_identity import AppIdentity


def _override_text(override_dir: str | Path | None, env_name: str) -> str:
    if override_dir is None:
        return str(os.getenv(env_name, "")).strip()
    return str(override_dir).strip()


def resolve_config_root(override_dir: str | Path | None = None) -> Path:
    """Resolve the root directory used for INI-backed QSettings storage."""

    override = _override_text(override_dir, "CONFIG_DIR")
    if override:
        root = Path(override).expanduser().resolve()
    elif os.name == "nt":
        fallback = Path(os.getenv("APPDATA", str(Path.home() / "AppData" / "Roaming")))
        root = fallback.expanduser().resolve()
    else:
        root = (Path.home() / ".config").expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_settings_dir(
    identity: AppIdentity, override_dir: str | Path | None = None
) -> Path:
    """Resolve the directory containing the app INI files."""

    settings_dir = resolve_config_root(override_dir) / identity.org_name
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir


def resolve_settings_file(
    identity: AppIdentity, override_dir: str | Path | None = None
) -> Path:
    """Resolve the app QSettings INI file path."""

    return resolve_settings_dir(identity, override_dir) / f"{identity.app_name}.ini"


def resolve_data_root(
    identity: AppIdentity, override_dir: str | Path | None = None
) -> Path:
    """Resolve the organization-scoped runtime data root directory."""

    override = _override_text(override_dir, "DATA_DIR")
    if override:
        root = Path(override).expanduser().resolve()
    elif os.name == "nt":
        fallback = Path(
            os.getenv("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        )
        root = fallback.expanduser().resolve() / identity.org_name
    else:
        root = (
            (Path.home() / ".local" / "share").expanduser().resolve()
        ) / identity.org_name
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_app_data_dir(
    identity: AppIdentity, override_dir: str | Path | None = None
) -> Path:
    """Resolve the app-scoped runtime data directory."""

    app_dir = resolve_data_root(identity, override_dir) / identity.app_name
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def resolve_log_dir(
    identity: AppIdentity, override_dir: str | Path | None = None
) -> Path:
    """Resolve the app log directory under runtime data storage."""

    log_dir = resolve_app_data_dir(identity, override_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def configure_qsettings(
    identity: AppIdentity,
    config_dir_override: str | Path | None = None,
) -> Path:
    """Configure global Qt QSettings INI storage for the supplied app identity."""

    config_root = resolve_config_root(config_dir_override)
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
        str(config_root),
    )
    return config_root
