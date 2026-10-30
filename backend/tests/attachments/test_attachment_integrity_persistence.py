"""TC-007.6 (persistence): the FAILURE audit row survives the request that ends in an error.

Uses the real ``get_db`` (rolls back on any exception) against a real PostgreSQL container.
"""

from __future__ import annotations

import hashlib
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

import app.db.models  # noqa: F401 — register all models
from app.api.deps import get_current_user
from app.api.routers.attachments import _get_attachment_service
from app.attachments.service import AttachmentService
from app.audit.service import AuditService
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.attachment import Attachment
from app.db.models.audit import AuditLog, AuditOutcome
from app.db.models.base import Base
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.session import get_db
from app.main import create_app


@pytest.fixture(scope="module")
def pg_engine():
    with PostgresContainer("postgres:16") as container:
        engine = create_engine(container.get_connection_url())
        Base.metadata.create_all(engine)
        yield engine
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_failure_audit_row_persists_after_502(pg_engine, monkeypatch) -> None:
    monkeypatch.setattr("app.db.repositories.session.get_engine", lambda: pg_engine)

    actor = MagicMock(spec=Account)
    actor.id = uuid.uuid4()
    actor.user_type = UserType.DOCTOR
    actor.status = AccountStatus.ACTIVE

    attachment = Attachment(
        id=uuid.uuid4(),
        clinical_entry_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        filename="a.pdf",
        content_type="application/pdf",
        size=8,
        storage_key="attachments/a.pdf",
        checksum=hashlib.sha256(b"original").hexdigest(),
    )

    def _service(db: Session = None) -> AttachmentService:  # type: ignore[assignment]
        repo = MagicMock()
        repo.get.return_value = attachment
        storage = MagicMock()
        storage.get_object.return_value = b"planted"
        return AttachmentService(
            repo,
            MagicMock(),
            AuditService(AuditRepository(db)),
            MagicMock(spec=AuthorizationService),
            storage,
        )

    from fastapi import Depends  # noqa: PLC0415

    def _dep(db: Session = Depends(get_db)) -> AttachmentService:
        return _service(db)

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[_get_attachment_service] = _dep

    resp = TestClient(app, raise_server_exceptions=False).get(
        f"/api/v1/attachments/{attachment.id}"
    )
    assert resp.status_code == 502

    with sessionmaker(bind=pg_engine)() as check:
        rows = (
            check.execute(select(AuditLog).where(AuditLog.target_id == str(attachment.id)))
            .scalars()
            .all()
        )
    assert len(rows) == 1
    assert rows[0].outcome == AuditOutcome.FAILURE
    assert rows[0].action == "ATTACHMENT_ACCESS"
    assert rows[0].actor_id == actor.id
