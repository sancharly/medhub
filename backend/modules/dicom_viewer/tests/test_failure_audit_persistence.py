"""TC-009.7 (real DB): the DICOM_STUDY_READ FAILURE row survives the 403 (PRB-052, ADR-0016).

Real ``get_db`` against a PostgreSQL container; the row is read back on a separate session.
Also checks the AC-23 declaration of the 502 on the study route.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from dicom_viewer.router import build_router
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

import app.db.models  # noqa: F401 — register all models
from app.api.deps import get_current_user, get_platform_services
from app.api.errors import AuthorizationError, register_error_handlers
from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.audit import AuditLog, AuditOutcome
from app.db.models.base import Base
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.session import get_db
from app.modules.platform_services import PlatformServices


@pytest.fixture(scope="module")
def pg_engine():
    with PostgresContainer("postgres:16") as container:
        engine = create_engine(container.get_connection_url())
        Base.metadata.create_all(engine)
        yield engine
        Base.metadata.drop_all(engine)
        engine.dispose()


def _app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(build_router(), prefix="/studies-test")
    return app


def test_dicom_study_read_failure_persists_after_403(pg_engine, monkeypatch) -> None:
    monkeypatch.setattr("app.db.repositories.session.get_engine", lambda: pg_engine)
    actor = MagicMock(spec=Account)
    actor.id = uuid.uuid4()
    actor.user_type = UserType.DOCTOR
    actor.status = AccountStatus.ACTIVE
    attachment_id = uuid.uuid4()

    def _services(db: Session = Depends(get_db)) -> PlatformServices:
        attachments = MagicMock()
        attachments.open.side_effect = AuthorizationError("Forbidden")
        return PlatformServices(
            authorization=MagicMock(),
            clinical=MagicMock(),
            attachments=attachments,
            audit=AuditService(AuditRepository(db)),
        )

    app = _app()
    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_platform_services] = _services

    resp = TestClient(app, raise_server_exceptions=False).get(
        f"/studies-test/studies/{attachment_id}"
    )

    assert resp.status_code == 403
    maker = sessionmaker(bind=pg_engine)
    with maker() as check:
        rows = list(
            check.execute(select(AuditLog).where(AuditLog.target_id == str(attachment_id)))
            .scalars()
            .all()
        )
    try:
        assert [(r.action, r.outcome, r.actor_id) for r in rows] == [
            (AuditAction.DICOM_STUDY_READ, AuditOutcome.FAILURE, actor.id)
        ]
    finally:
        with maker() as cleanup:
            cleanup.execute(delete(AuditLog))
            cleanup.commit()


def test_study_route_declares_502_problem_detail_body() -> None:
    """AC-23: the integrity-failure 502 is documented as application/problem+json."""
    responses = _app().openapi()["paths"]["/studies-test/studies/{attachment_id}"]["get"][
        "responses"
    ]
    schema = responses["502"]["content"]["application/problem+json"]["schema"]
    assert schema == {"$ref": "#/components/schemas/ProblemDetail"}
