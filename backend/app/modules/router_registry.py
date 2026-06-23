"""RouterRegistry — mounts module routers under /api/v1/modules/{module_key} (TASK-072)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, FastAPI

from app.api.deps import require_module_enabled

logger = logging.getLogger(__name__)

_MODULE_PREFIX = "/api/v1/modules"


class RouterRegistry:
    def __init__(self, app: FastAPI) -> None:
        self._app = app
        self._mounted: set[str] = set()

    def mount(self, module_key: str, router: APIRouter) -> None:
        """Mount router at /api/v1/modules/{module_key} with module-enablement gate."""
        if module_key in self._mounted:
            logger.warning(
                "Module %r already mounted — skipping duplicate registration", module_key
            )
            return

        prefix = f"{_MODULE_PREFIX}/{module_key}"
        gate = require_module_enabled(module_key)

        self._app.include_router(
            router,
            prefix=prefix,
            dependencies=[Depends(gate)],
        )
        self._mounted.add(module_key)
        logger.info("Mounted module %r at %s", module_key, prefix)
