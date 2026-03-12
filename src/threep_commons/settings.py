"""Shared QSettings storage and manager primitives."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, TypeVar, cast

from .app_identity import AppIdentity
from .qsettings_store import create_qsettings

_T = TypeVar("_T")


class QSettingsJsonStorage:
    """Thin QSettings wrapper with JSON helpers and deterministic path access."""

    def __init__(
        self,
        identity: AppIdentity,
        *,
        app_name: str | None = None,
        config_dir_override: str | Path | None = None,
    ) -> None:
        self.qsettings = create_qsettings(
            identity,
            app_name=app_name,
            config_dir_override=config_dir_override,
        )
        self.qsettings.sync()
        self.settings_path = Path(str(self.qsettings.fileName() or ""))

    def sync(self) -> None:
        self.qsettings.sync()

    def value(self, key: str, default: Any = None) -> Any:
        return self.qsettings.value(key, default)

    def set_value(self, key: str, value: Any) -> None:
        self.qsettings.setValue(key, value)

    def remove(self, key: str) -> None:
        self.qsettings.remove(key)

    def clear_all(self) -> None:
        self.qsettings.clear()

    def set_json(self, key: str, value: Any) -> None:
        self.qsettings.setValue(key, json.dumps(value))

    def get_json(self, key: str, default: Any) -> Any:
        raw = self.qsettings.value(key)
        if raw is None:
            return default
        if isinstance(raw, dict):
            return dict(cast("dict[str, Any]", raw))
        if isinstance(raw, list):
            return list(cast("list[Any]", raw))
        try:
            return json.loads(str(raw))
        except json.JSONDecodeError:
            return default


class SettingsDomainBase:
    """Shared base for one settings domain backed by one storage object."""

    def __init__(self, storage: QSettingsJsonStorage) -> None:
        self._storage = storage

    def _value(
        self,
        key: str,
        default: Any = None,
        *,
        normalize: Callable[[Any], _T] | None = None,
    ) -> Any | _T:
        raw = self._storage.value(key, default)
        if normalize is None:
            return raw
        return normalize(raw)

    def _set_value(
        self,
        key: str,
        value: Any,
        *,
        normalize: Callable[[Any], Any] | None = None,
    ) -> None:
        stored = normalize(value) if normalize is not None else value
        self._storage.set_value(key, stored)

    def _json(
        self,
        key: str,
        default: Any,
        *,
        normalize: Callable[[Any], _T] | None = None,
    ) -> Any | _T:
        raw = self._storage.get_json(key, default)
        if normalize is None:
            return raw
        return normalize(raw)

    def _set_json(
        self,
        key: str,
        value: Any,
        *,
        normalize: Callable[[Any], Any] | None = None,
    ) -> None:
        stored = normalize(value) if normalize is not None else value
        self._storage.set_json(key, stored)


def delegate_domain_property(domain_attr: str, name: str) -> property:
    """Build one facade property delegated to one composed settings domain."""

    return property(
        lambda self: getattr(getattr(self, domain_attr), name),
        lambda self, value: setattr(getattr(self, domain_attr), name, value),
    )


class SettingsManagerBase:
    """Shared facade methods around one composed settings storage object."""

    def __init__(self, storage: QSettingsJsonStorage) -> None:
        self._storage = storage
        self.settings_path = storage.settings_path

    def sync(self) -> None:
        self._storage.sync()

    def value(self, key: str, default: Any = None) -> Any:
        return self._storage.value(key, default)

    def set_value(self, key: str, value: Any) -> None:
        self._storage.set_value(key, value)

    def remove(self, key: str) -> None:
        self._storage.remove(key)

    def set_json(self, key: str, value: Any) -> None:
        self._storage.set_json(key, value)

    def get_json(self, key: str, default: Any) -> Any:
        return self._storage.get_json(key, default)

    def clear_all(self) -> None:
        self._storage.clear_all()
