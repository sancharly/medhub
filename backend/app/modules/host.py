"""Module host — registers all discovered modules into the FastAPI app (TASK-072)."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app.modules.contract import ModuleManifest
from app.modules.router_registry import RouterRegistry

logger = logging.getLogger(__name__)


def register_all_modules(app: FastAPI, manifests: list[ModuleManifest]) -> None:
    """For each manifest: build a RouterRegistry and call manifest.register().

    PlatformServices are injected per-request via FastAPI DI, not at startup.
    """
    for manifest in manifests:
        registry = RouterRegistry(app)
        try:
            manifest.register(registry, None)  # type: ignore[arg-type]
        except Exception:
            logger.exception("Failed to register module %r — skipping", manifest.module_key)
