"""Shared QSettings value-store and manager primitives."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, TypeVar, cast

from PySide6.QtCore import QSettings

from .app_identity import AppIdentity
from .config_helpers import SchemaEntry, coerce_value
from .qsettings_store import create_qsettings

_T = TypeVar("_T")


class QSettingsValueStore:
    """Typed QSettings wrapper with optional key namespace support."""

    def __init__(self, qsettings: QSettings, *, namespace: str | None = None) -> None:
        self.qsettings = qsettings
        self._namespace = self._normalize_namespace(namespace)
        self.qsettings.sync()
        self.settings_path = Path(self.file_name())

    @classmethod
    def from_identity(
        cls,
        identity: AppIdentity,
        *,
        app_name: str | None = None,
        config_dir_override: str | Path | None = None,
        namespace: str | None = None,
    ) -> QSettingsValueStore:
        return cls(
            create_qsettings(
                identity,
                app_name=app_name,
                config_dir_override=config_dir_override,
            ),
            namespace=namespace,
        )

    @staticmethod
    def _normalize_namespace(namespace: str | None) -> str:
        return str(namespace or "").strip().strip("/")

    @staticmethod
    def _coerce_list(value: Any, default: list[Any] | None = None) -> list[Any]:
        if value is None:
            return list(default or [])
        if isinstance(value, list):
            return list(value)
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, str):
            if value == "":
                return []
            return [value]
        return [value]

    def _full_key(self, key: str) -> str:
        cleaned = str(key or "").strip().strip("/")
        if not self._namespace:
            return cleaned
        if not cleaned:
            return self._namespace
        return f"{self._namespace}/{cleaned}"

    def file_name(self) -> str:
        return str(self.qsettings.fileName() or "").strip()

    def sync(self) -> None:
        self.qsettings.sync()

    def contains(self, key: str) -> bool:
        return self.qsettings.contains(self._full_key(key))

    def value(self, key: str, default: Any = None) -> Any:
        return self.qsettings.value(self._full_key(key), default)

    def set_value(self, key: str, value: Any) -> None:
        self.qsettings.setValue(self._full_key(key), value)

    def remove(self, key: str) -> None:
        self.qsettings.remove(self._full_key(key))

    def clear_all(self) -> None:
        target = self._full_key("")
        if target:
            self.qsettings.remove(target)
            return
        self.qsettings.clear()

    def child_groups(self, key: str = "") -> list[str]:
        target = self._full_key(key)
        if not target:
            return [str(group) for group in self.qsettings.childGroups()]
        self.qsettings.beginGroup(target)
        try:
            return [str(group) for group in self.qsettings.childGroups()]
        finally:
            self.qsettings.endGroup()

    def set_json(self, key: str, value: Any) -> None:
        self.qsettings.setValue(self._full_key(key), json.dumps(value))

    def get_json(self, key: str, default: Any) -> Any:
        raw = self.qsettings.value(self._full_key(key))
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

    def get_bool(self, key: str, default: bool = False) -> bool:
        if not self.contains(key):
            return bool(default)
        raw = self.value(key, default)
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, (int, float)):
            return bool(raw)
        if isinstance(raw, str):
            return raw.strip().lower() in {"1", "true", "yes", "on"}
        return bool(default)

    def get_str_list(self, key: str, default: list[str] | None = None) -> list[str]:
        if default is None and not self.contains(key):
            return []
        raw = self.value(key, default if default is not None else [])
        return [str(item) for item in self._coerce_list(raw, default)]

    def get_int_list(
        self, key: str, default: list[int] | None = None
    ) -> list[int] | None:
        if default is None and not self.contains(key):
            return None
        raw = self.value(key, default if default is not None else [])
        values: list[int] = []
        for item in self._coerce_list(raw, default):
            try:
                values.append(int(item))
            except (TypeError, ValueError):
                continue
        return values


def ensure_schema_defaults(
    settings: QSettingsValueStore | QSettings,
    schema: tuple[SchemaEntry, ...] | list[SchemaEntry],
) -> bool:
    """Seed missing schema keys into one QSettings-backed store."""

    store = (
        settings
        if isinstance(settings, QSettingsValueStore)
        else QSettingsValueStore(settings)
    )
    changed = False
    for key, expected_type, default in schema:
        if store.contains(key):
            continue
        store.set_value(key, coerce_value(default, expected_type, default))
        changed = True
    if changed:
        store.sync()
    return changed


class SettingsDomainBase:
    """Shared base for one settings domain backed by one storage object."""

    def __init__(self, storage: QSettingsValueStore) -> None:
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

    def __init__(self, storage: QSettingsValueStore) -> None:
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
