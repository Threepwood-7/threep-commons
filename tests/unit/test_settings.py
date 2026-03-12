"""Tests for shared QSettings settings primitives."""

from __future__ import annotations

import json

from threep_commons import AppIdentity
from threep_commons.settings import (
    QSettingsValueStore,
    QSettingsJsonStorage,
    SettingsDomainBase,
    SettingsManagerBase,
    delegate_domain_property,
    ensure_schema_defaults,
)
from threep_commons.qsettings_store import create_qsettings


class _FlagDomain(SettingsDomainBase):
    @property
    def enabled(self) -> bool:
        return bool(self._value("demo/enabled", False))

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._set_value("demo/enabled", bool(value))


class _FlagManager(SettingsManagerBase):
    enabled = delegate_domain_property("flags", "enabled")

    def __init__(self, storage: QSettingsJsonStorage) -> None:
        super().__init__(storage)
        self.flags = _FlagDomain(self._storage)


def test_qsettings_json_storage_roundtrips_json(tmp_path) -> None:
    identity = AppIdentity("ThreepSoftwz", "demo_settings", "Demo Settings")
    storage = QSettingsJsonStorage(identity, config_dir_override=tmp_path / "cfg")

    storage.set_json("demo/payload", {"ok": True})

    assert storage.get_json("demo/payload", {}) == {"ok": True}


def test_settings_manager_base_delegates_domain_properties(tmp_path) -> None:
    identity = AppIdentity("ThreepSoftwz", "demo_settings", "Demo Settings")
    storage = QSettingsJsonStorage(identity, config_dir_override=tmp_path / "cfg")
    manager = _FlagManager(storage)

    manager.enabled = True

    assert manager.enabled is True


def test_qsettings_value_store_typed_helpers_and_namespace(tmp_path) -> None:
    identity = AppIdentity("ThreepSoftwz", "demo_settings", "Demo Settings")
    store = QSettingsValueStore.from_identity(
        identity,
        config_dir_override=tmp_path / "cfg",
        namespace="prefs",
    )

    store.set_value("enabled", "true")
    store.set_value("tags", ["a", "b"])
    store.set_value("numbers", ["1", "bad", 3])
    store.set_json("payload", {"ok": True})
    store.sync()

    assert store.get_bool("enabled") is True
    assert store.get_str_list("tags") == ["a", "b"]
    assert store.get_int_list("numbers") == [1, 3]
    assert store.get_json("payload", {}) == {"ok": True}
    assert store.file_name().endswith("demo_settings.ini")

    raw_settings = create_qsettings(identity, config_dir_override=tmp_path / "cfg")
    assert raw_settings.value("prefs/payload") == json.dumps({"ok": True})


def test_ensure_schema_defaults_accepts_value_store(tmp_path) -> None:
    identity = AppIdentity("ThreepSoftwz", "demo_settings", "Demo Settings")
    store = QSettingsValueStore.from_identity(
        identity,
        config_dir_override=tmp_path / "cfg",
        namespace="demo",
    )

    changed = ensure_schema_defaults(
        store,
        [
            ("enabled", bool, True),
            ("count", int, 3),
        ],
    )

    assert changed is True
    assert store.get_bool("enabled") is True
    assert store.value("count") == 3
