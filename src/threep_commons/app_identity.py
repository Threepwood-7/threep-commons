"""Application identity metadata shared across runtime helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AppIdentity:
    """Describe the stable identity and runtime logging defaults for one app."""

    org_name: str
    app_name: str
    display_name: str
    default_log_filename: str = "app.log"
    default_log_max_bytes: int = 1_048_576
    default_log_backup_count: int = 3
