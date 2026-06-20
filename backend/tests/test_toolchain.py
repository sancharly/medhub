"""TASK-001: Verify all sub-packages are importable."""
import importlib

PACKAGES = [
    "app",
    "app.core",
    "app.db",
    "app.db.models",
    "app.db.repositories",
    "app.api",
    "app.auth",
    "app.authz",
    "app.identity",
    "app.groups",
    "app.clinical",
    "app.attachments",
    "app.appointments",
    "app.audit",
    "app.modules",
    "app.workers",
]


def test_all_packages_importable() -> None:
    for pkg in PACKAGES:
        mod = importlib.import_module(pkg)
        assert mod is not None, f"Failed to import {pkg}"
