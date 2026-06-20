"""MedHub API application factory."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.router import api_router
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    # Import here to avoid settings being loaded at module import time in tests
    from app.core.config import get_settings  # noqa: PLC0415

    settings = get_settings()
    logger.info(
        "MedHub API starting up",
        extra={
            "environment": settings.environment,
            "cors_origins": settings.cors_origins,
        },
    )
    yield
    logger.info("MedHub API shutting down")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="MedHub API",
        version="0.1.0",
        openapi_url="/api/v1/openapi.json",
        lifespan=_lifespan,
        servers=[{"url": "/", "description": "Default server"}],
        license_info={"name": "Proprietary"},
    )
    app.include_router(api_router)
    app.include_router(health_router)

    _patch_openapi(app)
    return app


def _patch_openapi(app: FastAPI) -> None:
    """Add fields required by the Redocly recommended ruleset."""
    original_openapi = app.openapi

    def patched_openapi() -> dict:
        schema = original_openapi()
        # Root-level security: [] means "no auth required by default"
        schema.setdefault("security", [])
        # Ensure health endpoint declares a 4XX response
        healthz_op = schema.get("paths", {}).get("/healthz", {}).get("get")
        if healthz_op and "422" not in healthz_op.get("responses", {}):
            healthz_op["responses"]["422"] = {
                "description": "Unprocessable Entity",
            }
        return schema

    app.openapi = patched_openapi  # type: ignore[method-assign]


app = create_app()
