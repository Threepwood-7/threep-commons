"""Tests for shared file helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from threep_commons import AppIdentity
from threep_commons.files import (
    append_instance_id_to_filename,
    append_suffix_before_extension,
    build_instance_app_name,
    resolve_cache_file_path,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_append_suffix_helpers() -> None:
    assert append_suffix_before_extension("demo.log", "x") == "demo_x.log"
    assert append_instance_id_to_filename("demo.log", "abc_1") == "demo_abc_1.log"


def test_build_instance_app_name() -> None:
    assert build_instance_app_name("demo_app", "") == "demo_app"
    assert build_instance_app_name("demo_app", "abc_1") == "demo_app_abc_1"


def test_resolve_cache_file_path(tmp_path: Path) -> None:
    identity = AppIdentity("ThreepSoftwz", "demo_app", "Demo App")

    cache_path = resolve_cache_file_path(
        identity,
        "cache.json",
        instance_id="abc_1",
        data_dir_override=tmp_path / "data",
    )

    assert cache_path == (tmp_path / "data" / "demo_app" / "cache_abc_1.json").resolve()
