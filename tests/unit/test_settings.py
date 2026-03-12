"""Tests for shared QSettings settings primitives."""

from __future__ import annotations

from threep_commons import AppIdentity
from threep_commons.settings import (
    QSettingsJsonStorage,
    SettingsDomainBase,
    SettingsManagerBase,
    delegate_domain_property,
)


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
