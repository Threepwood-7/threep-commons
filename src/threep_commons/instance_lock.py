"""Shared instance-id and OS file-lock helpers."""

from __future__ import annotations

import hashlib
import os
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

from .files import resolve_cache_file_path

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .app_identity import AppIdentity

_INSTANCE_LOCK_HANDLES: dict[str, BinaryIO] = {}


def normalize_instance_host(raw_host: object) -> str:
    """Normalize one host value used for per-instance identifiers."""

    if raw_host is None:
        return "localhost"
    host = str(raw_host).strip()
    return host if host else "localhost"


def normalize_instance_port(raw_port: object) -> int:
    """Normalize one TCP port value used for per-instance identifiers."""

    if isinstance(raw_port, (int, float, str, bytes, bytearray)):
        try:
            port = int(raw_port)
        except (TypeError, ValueError, OverflowError):
            port = 8080
    else:
        port = 8080
    if port < 1 or port > 65535:
        return 8080
    return port


def normalize_instance_counter(raw_counter: object) -> int:
    """Normalize one positive per-instance counter."""

    if isinstance(raw_counter, (int, float, str, bytes, bytearray)):
        try:
            counter = int(raw_counter)
        except (TypeError, ValueError, OverflowError):
            counter = 1
    else:
        counter = 1
    return counter if counter > 0 else 1


def normalize_http_protocol_scheme(raw_scheme: object) -> str:
    """Normalize one HTTP protocol scheme to `http` or `https`."""

    scheme = str(raw_scheme or "").strip().lower()
    if scheme in {"http", "https"}:
        return scheme
    return "http"


def compute_instance_id(
    host: object,
    port: object,
    *,
    length: int = 8,
    instance_counter: object = 1,
) -> str:
    """Compute a stable short instance id from host, port, and counter."""

    normalized_host = normalize_instance_host(host)
    normalized_port = normalize_instance_port(port)
    digest = hashlib.sha1(f"{normalized_host}:{normalized_port}".encode()).hexdigest()
    try:
        max_len = max(1, int(length))
    except (TypeError, ValueError, OverflowError):
        max_len = 8
    base_id = digest[:max_len]
    counter = normalize_instance_counter(instance_counter)
    return f"{base_id}_{counter}"


def compute_instance_id_from_mapping(
    config: Mapping[str, object],
    *,
    host_keys: tuple[str, ...] = ("qb_host", "host"),
    port_keys: tuple[str, ...] = ("qb_port", "port"),
    counter_key: str = "_instance_counter",
    length: int = 8,
) -> str:
    """Compute one instance id from a config mapping and common host/port keys."""

    host = next((config[key] for key in host_keys if key in config), "localhost")
    port = next((config[key] for key in port_keys if key in config), 8080)
    counter = config.get(counter_key, 1)
    return compute_instance_id(host, port, length=length, instance_counter=counter)


def _lock_handle_key(lock_path: Path) -> str:
    try:
        return str(lock_path.resolve())
    except (OSError, RuntimeError, ValueError):
        return str(lock_path)


def _try_acquire_os_file_lock(handle: BinaryIO) -> bool:
    try:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            return True

        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except (AttributeError, ImportError, OSError, ValueError):
        return False


def _release_os_file_lock(handle: BinaryIO) -> None:
    try:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            return

        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except (AttributeError, ImportError, OSError, ValueError):
        return


def resolve_instance_lock_file_path(
    identity: AppIdentity,
    instance_id: str,
    instance_counter: object,
    *,
    lock_file_name: str = "app.lock",
    data_dir_override: str | Path | None = None,
) -> Path:
    """Resolve one per-instance lock file path below app data."""

    ident = str(instance_id or "").strip().lower()
    counter = normalize_instance_counter(instance_counter)
    suffix = f"_{counter}"
    lock_key = ident if ident.endswith(suffix) else f"{ident}{suffix}"
    return resolve_cache_file_path(
        identity,
        lock_file_name,
        instance_id=lock_key,
        data_dir_override=data_dir_override,
    )


def acquire_instance_lock(
    identity: AppIdentity,
    config: Mapping[str, object],
    start_counter: object,
    *,
    lock_file_name: str = "app.lock",
    host_keys: tuple[str, ...] = ("qb_host", "host"),
    port_keys: tuple[str, ...] = ("qb_port", "port"),
    counter_key: str = "_instance_counter",
    length: int = 8,
    data_dir_override: str | Path | None = None,
) -> tuple[int, str, Path]:
    """Acquire one exclusive instance lock, incrementing the counter when needed."""

    counter = normalize_instance_counter(start_counter)
    config_data = dict(config)

    while True:
        config_data[counter_key] = int(counter)
        instance_id = compute_instance_id_from_mapping(
            config_data,
            host_keys=host_keys,
            port_keys=port_keys,
            counter_key=counter_key,
            length=length,
        )
        lock_path = resolve_instance_lock_file_path(
            identity,
            instance_id,
            counter,
            lock_file_name=lock_file_name,
            data_dir_override=data_dir_override,
        )
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            handle = lock_path.open("a+b")
        except OSError as exc:
            raise RuntimeError(f"Failed to open lock file {lock_path}: {exc}") from exc

        try:
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\n")
                handle.flush()
            handle.seek(0)
            if not _try_acquire_os_file_lock(handle):
                handle.close()
                counter += 1
                continue

            payload = (
                f"instance_id={instance_id}\ninstance_counter={counter}\n".encode()
            )
            handle.seek(0)
            handle.truncate(0)
            handle.write(payload)
            handle.flush()
            with suppress(OSError):
                os.fsync(handle.fileno())

            _INSTANCE_LOCK_HANDLES[_lock_handle_key(lock_path)] = handle
            return int(counter), instance_id, lock_path
        except (OSError, ValueError, RuntimeError):
            with suppress(OSError):
                handle.close()
            raise


def release_instance_lock(lock_path: Path) -> None:
    """Release and remove one instance lock file when present."""

    key = _lock_handle_key(Path(lock_path))
    handle = _INSTANCE_LOCK_HANDLES.pop(key, None)
    if handle is not None:
        try:
            _release_os_file_lock(handle)
        finally:
            with suppress(OSError):
                handle.close()
    try:
        Path(lock_path).unlink()
    except FileNotFoundError:
        pass
    except OSError:
        return
