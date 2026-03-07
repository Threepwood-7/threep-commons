"""Tests for shared instance-lock helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from threep_commons import AppIdentity
from threep_commons.instance_lock import (
    acquire_instance_lock,
    compute_instance_id,
    compute_instance_id_from_mapping,
    normalize_http_protocol_scheme,
    normalize_instance_counter,
    release_instance_lock,
    resolve_instance_lock_file_path,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_compute_instance_id_helpers() -> None:
    config = {"qb_host": "127.0.0.1", "qb_port": 8080, "_instance_counter": 2}

    assert compute_instance_id("127.0.0.1", 8080, instance_counter=2).endswith("_2")
    assert compute_instance_id_from_mapping(config).endswith("_2")
    assert normalize_instance_counter("3") == 3
    assert normalize_http_protocol_scheme("HTTPS") == "https"


def test_acquire_and_release_instance_lock(tmp_path: Path) -> None:
    identity = AppIdentity("ThreepSoftwz", "demo_app", "Demo App")
    config = {"qb_host": "127.0.0.1", "qb_port": 8080}

    counter1, instance_id1, lock_path1 = acquire_instance_lock(
        identity,
        config,
        1,
        lock_file_name="demo.lock",
        data_dir_override=tmp_path / "data",
    )
    counter2, instance_id2, lock_path2 = acquire_instance_lock(
        identity,
        config,
        1,
        lock_file_name="demo.lock",
        data_dir_override=tmp_path / "data",
    )

    assert counter1 == 1
    assert counter2 == 2
    assert instance_id1 != instance_id2
    assert lock_path1.is_file()
    assert lock_path2.is_file()
    assert (
        resolve_instance_lock_file_path(
            identity,
            instance_id1,
            counter1,
            lock_file_name="demo.lock",
            data_dir_override=tmp_path / "data",
        )
        == lock_path1
    )

    release_instance_lock(lock_path1)
    release_instance_lock(lock_path2)

    assert not lock_path1.exists()
    assert not lock_path2.exists()
