"""Windows-specific storage and volume helpers."""

from .storage import (
    WindowsStorageUsage,
    is_local_windows_path,
    list_windows_storage_roots,
    list_windows_storage_usage,
    normalized_path_key,
    resolve_physical_disk_numbers,
    resolve_physical_disk_tokens,
    resolve_volume_identity,
)
from .volumes import (
    get_volume_guid_path,
    get_volume_mount_point,
    list_logical_drive_roots,
    list_mounted_volume_paths,
    list_volume_mount_points,
)

__all__ = [
    "WindowsStorageUsage",
    "get_volume_guid_path",
    "get_volume_mount_point",
    "is_local_windows_path",
    "list_logical_drive_roots",
    "list_mounted_volume_paths",
    "list_volume_mount_points",
    "list_windows_storage_roots",
    "list_windows_storage_usage",
    "normalized_path_key",
    "resolve_physical_disk_numbers",
    "resolve_physical_disk_tokens",
    "resolve_volume_identity",
]

