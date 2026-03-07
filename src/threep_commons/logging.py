"""Shared logging configuration helpers."""

from __future__ import annotations

import atexit
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING

from .files import append_instance_id_to_filename
from .paths import resolve_log_dir

if TYPE_CHECKING:
    from types import TracebackType

    from .app_identity import AppIdentity

DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def build_log_formatter(
    fmt: str = DEFAULT_LOG_FORMAT,
    datefmt: str = DEFAULT_LOG_DATE_FORMAT,
) -> logging.Formatter:
    """Build a standard log formatter shared across the app family."""

    return logging.Formatter(fmt=fmt, datefmt=datefmt)


def resolve_log_path(
    identity: AppIdentity,
    raw_log_file: str,
    *,
    instance_id: str = "",
    data_dir_override: str | Path | None = None,
) -> Path:
    """Resolve one log file path using the app identity defaults."""

    path_obj = Path(str(raw_log_file).strip()).expanduser()
    if not path_obj.is_absolute():
        path_obj = resolve_log_dir(identity, data_dir_override) / path_obj
    if instance_id:
        path_obj = Path(append_instance_id_to_filename(path_obj, instance_id))
    return path_obj


def setup_logging(
    log_dir: Path,
    *,
    log_filename: str = "app.log",
    max_bytes: int = 1_048_576,
    backup_count: int = 3,
    level: int = logging.INFO,
    console: bool = True,
) -> Path:
    """Configure root logging with one rotating file handler and optional console output."""

    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_filename

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    formatter = build_log_formatter()

    file_handler = RotatingFileHandler(
        filename=Path(log_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    return log_path


def setup_logging_from_identity(
    identity: AppIdentity,
    *,
    data_dir_override: str | Path | None = None,
    log_filename: str | None = None,
    max_bytes: int | None = None,
    backup_count: int | None = None,
    level: int = logging.INFO,
    console: bool = True,
) -> Path:
    """Configure root logging using defaults from one app identity."""

    return setup_logging(
        resolve_log_dir(identity, data_dir_override),
        log_filename=log_filename or identity.default_log_filename,
        max_bytes=max_bytes or identity.default_log_max_bytes,
        backup_count=backup_count or identity.default_log_backup_count,
        level=level,
        console=console,
    )


def setup_logger_to_file(
    logger: logging.Logger,
    log_path: Path,
    *,
    level: int = logging.DEBUG,
    console: bool = False,
    clear_handlers: bool = True,
    formatter: logging.Formatter | None = None,
) -> logging.FileHandler:
    """Attach one file handler to a specific logger and optionally mirror to console."""

    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(
        formatter
        or build_log_formatter(
            fmt="%(asctime)s %(levelname)-7s %(message)s",
            datefmt=DEFAULT_LOG_DATE_FORMAT,
        )
    )

    if clear_handlers:
        logger.handlers.clear()
    logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(build_log_formatter())
        logger.addHandler(console_handler)

    logger.setLevel(level)
    logger.propagate = False
    return file_handler


def install_exception_hooks(
    logger: logging.Logger, file_handler: logging.Handler
) -> None:
    """Install a process-wide excepthook that logs and flushes fatal errors."""

    def _excepthook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType | None,
    ) -> None:
        if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
        file_handler.flush()

    sys.excepthook = _excepthook
    atexit.register(file_handler.flush)
