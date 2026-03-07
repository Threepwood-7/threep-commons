"""Tests for shared logging helpers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from threep_commons import AppIdentity
from threep_commons.logging import (
    install_exception_hooks,
    resolve_log_path,
    setup_logger_to_file,
    setup_logging_from_identity,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_setup_logging_from_identity_creates_log_path(tmp_path: Path) -> None:
    identity = AppIdentity(
        "ThreepSoftwz",
        "demo_app",
        "Demo App",
        default_log_filename="demo.log",
    )

    log_path = setup_logging_from_identity(
        identity, data_dir_override=tmp_path / "data"
    )
    logging.getLogger().info("hello")

    assert log_path == (tmp_path / "data" / "demo_app" / "logs" / "demo.log").resolve()
    assert len(logging.getLogger().handlers) == 2
    logging.getLogger().handlers.clear()


def test_setup_logger_to_file_and_exception_hook(tmp_path: Path) -> None:
    logger = logging.getLogger("threep_commons.tests.logger")
    log_path = tmp_path / "demo.log"
    file_handler = setup_logger_to_file(logger, log_path)
    install_exception_hooks(logger, file_handler)

    logger.error("demo")
    file_handler.flush()

    assert log_path.read_text(encoding="utf-8")
    logger.handlers.clear()


def test_resolve_log_path_for_instance(tmp_path: Path) -> None:
    identity = AppIdentity("ThreepSoftwz", "demo_app", "Demo App")

    log_path = resolve_log_path(
        identity,
        "demo.log",
        instance_id="abc_1",
        data_dir_override=tmp_path / "data",
    )

    assert log_path.name == "demo_abc_1.log"
