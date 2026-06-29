"""MedHub API application factory."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import register_error_handlers
from app.api.health import router as health_router
from app.api.router import api_router
from app.core.logging import configure_logging
from app.core.security_middleware import CsrfEnforcementMiddleware, SecurityHeadersMiddleware

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

    # Module discovery and registration
    from app.modules.discovery import discover_modules  # noqa: PLC0415
    from app.modules.host import register_all_modules  # noqa: PLC0415

    manifests = discover_modules()
    if manifests:
        register_all_modules(app, manifests)

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
    register_error_handlers(app)

    # Security middleware (TASK-069)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CsrfEnforcementMiddleware)

    # OpenAPI customization (TASK-068)
    from app.api.openapi import customize_openapi  # noqa: PLC0415

    customize_openapi(app)

    return app


app = create_app()
