"""TC-007.6 (persistence): the FAILURE audit row survives the request that ends in an error.

Uses the real ``get_db`` (rolls back on any exception) against a real PostgreSQL container.
"""

from __future__ import annotations

import hashlib
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

import app.db.models  # noqa: F401 — register all models
from app.api.deps import get_current_user
from app.api.routers.attachments import _get_attachment_service
from app.attachments.service import AttachmentService
from app.audit.service import AuditService
from app.authz.service import AuthorizationService
from app.db import roles
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


@pytest.fixture(scope="module")
def runtime_engine(pg_engine):
    """The engine the application runs on: the runtime role of ADR-0017 (TASK-190, AC 2).

    ``pg_engine`` stays the owner connection, used for set-up, read-back and clean-up (the
    runtime role cannot delete ``audit_log`` rows).
    """
    roles.apply(pg_engine, "medhub_app", "runtime-pw-4k9x2m7q")
    engine = create_engine(pg_engine.url.set(username="medhub_app", password="runtime-pw-4k9x2m7q"))
    yield engine
    engine.dispose()


def _download(
    pg_engine,
    runtime_engine,
    monkeypatch,
    *,
    storage_data=b"original",
    storage_error: Exception | None = None,
    filename: str = "a.pdf",
):
    """Run GET /attachments/{id} on the real ``get_db`` against the runtime role."""
    monkeypatch.setattr("app.db.repositories.session.get_engine", lambda: runtime_engine)

    actor = MagicMock(spec=Account)
    actor.id = uuid.uuid4()
    actor.user_type = UserType.DOCTOR
    actor.status = AccountStatus.ACTIVE

    attachment = Attachment(
        id=uuid.uuid4(),
        clinical_entry_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        filename=filename,
        content_type="application/pdf",
        size=8,
        storage_key="attachments/a.pdf",
        checksum=hashlib.sha256(b"original").hexdigest(),
    )

    def _service(db: Session = None) -> AttachmentService:  # type: ignore[assignment]
        repo = MagicMock()
        repo.get.return_value = attachment
        storage = MagicMock()
        storage.get_object.return_value = storage_data
        if storage_error is not None:
            storage.get_object.side_effect = storage_error
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
    return resp, attachment, actor


def _rows_and_clean(pg_engine, attachment) -> list[AuditLog]:
    with sessionmaker(bind=pg_engine)() as check:
        rows = list(
            check.execute(select(AuditLog).where(AuditLog.target_id == str(attachment.id)))
            .scalars()
            .all()
        )
    # Independent rows commit outside any test transaction; leave the table clean. The owner
    # connection deletes them: the runtime role cannot (SR-023 AC 8).
    with sessionmaker(bind=pg_engine)() as cleanup:
        cleanup.execute(delete(AuditLog))
        cleanup.commit()
    return rows


def test_failure_audit_row_persists_after_502(pg_engine, runtime_engine, monkeypatch) -> None:
    resp, attachment, actor = _download(
        pg_engine, runtime_engine, monkeypatch, storage_data=b"planted"
    )
    assert resp.status_code == 502
    rows = _rows_and_clean(pg_engine, attachment)
    assert len(rows) == 1
    assert rows[0].outcome == AuditOutcome.FAILURE
    assert rows[0].action == "ATTACHMENT_ACCESS"
    assert rows[0].actor_id == actor.id
    assert rows[0].ip == "testclient"  # SR-023 AC 6: client address on a FAILURE row


def test_failure_audit_row_persists_after_storage_error(
    pg_engine, runtime_engine, monkeypatch
) -> None:
    """AC-3 (TC-007.10): storage raises -> 500, one committed FAILURE row."""
    resp, attachment, actor = _download(
        pg_engine, runtime_engine, monkeypatch, storage_error=RuntimeError("store down")
    )
    assert resp.status_code == 500
    rows = _rows_and_clean(pg_engine, attachment)
    assert len(rows) == 1
    assert rows[0].outcome == AuditOutcome.FAILURE
    assert rows[0].action == "ATTACHMENT_ACCESS"
    assert rows[0].actor_id == actor.id
    assert rows[0].ip == "testclient"  # SR-023 AC 6: client address on a FAILURE row


def test_failure_audit_row_persists_when_response_cannot_be_built(
    pg_engine, runtime_engine, monkeypatch
) -> None:
    """AC-3 (TC-007.10): the response build fails after a successful open -> FAILURE only."""

    def _boom(*_a, **_k):
        raise RuntimeError("cannot build header")

    monkeypatch.setattr("app.api.routers.attachments.content_disposition", _boom, raising=False)
    resp, attachment, actor = _download(pg_engine, runtime_engine, monkeypatch)
    assert resp.status_code == 500
    rows = _rows_and_clean(pg_engine, attachment)
    assert [r.outcome for r in rows] == [AuditOutcome.FAILURE]
    assert rows[0].action == "ATTACHMENT_ACCESS"
    assert rows[0].actor_id == actor.id
    assert rows[0].ip == "testclient"  # SR-023 AC 6: client address on a FAILURE row


def test_non_latin1_name_downloads_and_commits_success_row(
    pg_engine, runtime_engine, monkeypatch
) -> None:
    """AC-1 (TC-007.9): a name outside Latin-1 downloads and the SUCCESS row commits."""
    resp, attachment, actor = _download(
        pg_engine, runtime_engine, monkeypatch, filename="résumé 患者 #1.txt"
    )
    assert resp.status_code == 200
    assert resp.content == b"original"
    rows = _rows_and_clean(pg_engine, attachment)
    assert [r.outcome for r in rows] == [AuditOutcome.SUCCESS]
    assert rows[0].action == "ATTACHMENT_ACCESS"
    assert rows[0].actor_id == actor.id
