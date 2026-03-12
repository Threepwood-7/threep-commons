"""Shared filename and runtime-path helpers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .paths import resolve_app_data_dir

if TYPE_CHECKING:
    from .app_identity import AppIdentity


def append_suffix_before_extension(path_value: str | Path, suffix: str) -> str:
    """Append one suffix before the filename extension, preserving directories."""

    raw = str(path_value or "").strip()
    if not raw:
        return raw

    suffix_text = str(suffix or "").strip()
    if not suffix_text:
        return raw
    if not suffix_text.startswith("_"):
        suffix_text = f"_{suffix_text}"

    path_obj = Path(raw)
    if path_obj.stem.lower().endswith(suffix_text.lower()):
        return str(path_obj)

    if path_obj.suffix:
        new_name = f"{path_obj.stem}{suffix_text}{path_obj.suffix}"
    else:
        new_name = f"{path_obj.name}{suffix_text}"
    return str(path_obj.with_name(new_name))


def append_instance_id_to_filename(path_value: str | Path, instance_id: str) -> str:
    """Append one normalized instance id before the filename extension."""

    return append_suffix_before_extension(
        path_value, str(instance_id or "").strip().lower()
    )


def build_instance_app_name(base_app_name: str, instance_id: str) -> str:
    """Build an app name variant suffixed with one instance id."""

    ident = str(instance_id or "").strip().lower()
    if not ident:
        return base_app_name
    return f"{base_app_name}_{ident}"


def resolve_runtime_file_path(
    identity: AppIdentity,
    file_name: str | Path,
    *,
    subdir: str | None = None,
    instance_id: str = "",
    data_dir_override: str | Path | None = None,
) -> Path:
    """Resolve a runtime file path under app data unless an absolute path is supplied."""

    raw_path = Path(str(file_name)).expanduser()
    if instance_id:
        raw_path = Path(append_instance_id_to_filename(raw_path, instance_id))
    if raw_path.is_absolute():
        return raw_path

    base_dir = resolve_app_data_dir(identity, data_dir_override)
    if subdir:
        base_dir = base_dir / subdir
    return base_dir / raw_path


def resolve_cache_file_path(
    identity: AppIdentity,
    cache_file_name: str | Path,
    *,
    instance_id: str = "",
    data_dir_override: str | Path | None = None,
) -> Path:
    """Resolve a cache file path below the app data root."""

    return resolve_runtime_file_path(
        identity,
        cache_file_name,
        instance_id=instance_id,
        data_dir_override=data_dir_override,
    )
