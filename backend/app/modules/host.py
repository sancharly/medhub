"""Module host — registers all discovered modules into the FastAPI app (TASK-072)."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app.modules.contract import ModuleManifest, PlatformServices
from app.modules.router_registry import RouterRegistry

logger = logging.getLogger(__name__)


def register_all_modules(
    app: FastAPI,
    manifests: list[ModuleManifest],
    platform_services: PlatformServices,
) -> None:
    """For each manifest: build a RouterRegistry and call manifest.register()."""
    for manifest in manifests:
        registry = RouterRegistry(app)
        try:
            manifest.register(registry, platform_services)
        except Exception:
            logger.exception("Failed to register module %r — skipping", manifest.module_key)
