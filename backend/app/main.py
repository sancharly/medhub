"""MedHub API application factory."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import register_error_handlers
from app.api.health import router as health_router
from app.api.router import api_router
from app.core.client_address import ClientAddressMiddleware
from app.core.logging import configure_logging
from app.core.security_middleware import CsrfEnforcementMiddleware, SecurityHeadersMiddleware

logger = logging.getLogger(__name__)


def _bind_celery_app() -> None:
    """PRB-071: make the configured Celery app the default app of this API process.

    The tasks are ``@shared_task``, which bind to the current app, and a sync route runs in a worker
    thread. Importing the app only makes it current in the importing thread (thread-local), so a
    route's ``.delay()`` used Celery's built-in app and its ``amqp://localhost`` broker and failed.
    ``set_default()`` is process-global: every thread resolves the configured Redis broker.

    Called from the lifespan, so it runs once per gunicorn worker, after the secret rule, and
    settings are not read at import time (tests import this module without them). Building the app
    only connects receivers: the secret rule runs on ``worker_init``/``beat_init``, never here.
    """
    from app.workers.celery_app import celery_app  # noqa: PLC0415

    celery_app.set_default()


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    # Import here to avoid settings being loaded at module import time in tests
    from app.core.config import get_settings  # noqa: PLC0415
    from app.core.secret_settings import enforce  # noqa: PLC0415

    # SR-041 AC 3: refuse missing or placeholder secrets before anything else starts.
    enforce()
    _bind_celery_app()

    settings = get_settings()
    logger.info(
        "MedHub API starting up",
        extra={
            "environment": settings.environment,
            "cors_origins": settings.cors_origins,
        },
    )

    # Module discovery, registry sync, and registration
    from app.audit.service import AuditService  # noqa: PLC0415
    from app.db.repositories.audit_repo import AuditRepository  # noqa: PLC0415
    from app.db.repositories.module_repo import ModuleRepository  # noqa: PLC0415
    from app.db.repositories.session import get_engine, get_session_factory  # noqa: PLC0415
    from app.modules.discovery import discover_modules  # noqa: PLC0415
    from app.modules.host import register_all_modules  # noqa: PLC0415
    from app.modules.registry_service import ModuleRegistryService  # noqa: PLC0415

    manifests = discover_modules()
    if manifests:
        _engine = get_engine()
        _SessionLocal = get_session_factory(_engine)
        _db = _SessionLocal()
        try:
            _registry_svc = ModuleRegistryService(
                ModuleRepository(_db),
                AuditService(AuditRepository(_db)),
            )
            _registry_svc.sync_installed(manifests, _db)
            _db.commit()
        except Exception:
            _db.rollback()
            logger.exception("Module registry sync failed at startup — modules unreachable")
            raise
        finally:
            _db.close()
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

    # Originating client address (TASK-185): added last, so it is the outermost middleware
    app.add_middleware(ClientAddressMiddleware)

    # OpenAPI customization (TASK-068)
    from app.api.openapi import customize_openapi  # noqa: PLC0415

    customize_openapi(app)

    return app


app = create_app()
