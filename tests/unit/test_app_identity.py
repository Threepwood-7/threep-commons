"""Tests for app identity metadata."""

from threep_commons import AppIdentity


def test_app_identity_defaults() -> None:
    identity = AppIdentity(
        org_name="ThreepSoftwz",
        app_name="demo_app",
        display_name="Demo App",
    )

    assert identity.org_name == "ThreepSoftwz"
    assert identity.app_name == "demo_app"
    assert identity.display_name == "Demo App"
    assert identity.default_log_filename == "app.log"
