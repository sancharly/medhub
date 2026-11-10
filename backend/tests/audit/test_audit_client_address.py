"""TC-009.9 (real DB): request-caused audit rows record the originating client address.

Requests go through ``create_app()`` with the real ``get_db`` against a PostgreSQL container
(SR-023 AC 6, SR-042 AC 2, ADR-0019, TASK-137). The proxy is trusted through ``TRUSTED_PROXIES``;
the TestClient peer address is set per test.
"""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Iterator
from unittest.mock import MagicMock

import fakeredis
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

import app.db.models  # noqa: F401 — register all models
from app.api.deps import get_current_user, get_redis
from app.api.routers.attachments import _get_attachment_service
from app.attachments.service import AttachmentService
from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.auth.password import PasswordService
from app.authz.service import AuthorizationService
from app.core.config import get_settings
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.attachment import Attachment
from app.db.models.audit import AuditLog
from app.db.models.base import Base
from app.db.models.consent import ConsentGrant
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.session import get_db
from app.main import create_app

PROXY = "10.0.0.2"
UNTRUSTED = "198.51.100.9"
CLIENT = "203.0.113.7"
FORGED = "1.2.3.4"


@pytest.fixture(scope="module")
def pg_engine():
    with PostgresContainer("postgres:16") as container:
        engine = create_engine(container.get_connection_url())
        Base.metadata.create_all(engine)
        yield engine
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def factory(pg_engine, monkeypatch) -> Iterator[sessionmaker[Session]]:
    monkeypatch.setattr("app.db.repositories.session.get_engine", lambda: pg_engine)
    monkeypatch.setenv("TRUSTED_PROXIES", PROXY)
    get_settings.cache_clear()
    maker = sessionmaker(bind=pg_engine)
    yield maker
    get_settings.cache_clear()
    with maker() as s:
        s.execute(delete(AuditLog))
        s.execute(delete(ConsentGrant))
        s.execute(delete(Account))
        s.commit()


@pytest.fixture
def app_(factory):
    application = create_app()
    redis = fakeredis.FakeRedis()
    application.dependency_overrides[get_redis] = lambda: redis
    return application


def _client(application, peer: str) -> TestClient:
    return TestClient(application, raise_server_exceptions=False, client=(peer, 5000))


def _rows(factory, **filters) -> list[AuditLog]:
    with factory() as check:
        stmt = select(AuditLog)
        for col, val in filters.items():
            stmt = stmt.where(getattr(AuditLog, col) == val)
        return list(check.execute(stmt).scalars().all())


def _make_account(factory, user_type: UserType) -> Account:
    acct = Account(
        email=f"{uuid.uuid4().hex}@example.com",
        password_hash=PasswordService().hash("Correct-Horse-Battery-9!"),
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )
    with factory() as s:
        s.add(acct)
        s.commit()
        s.refresh(acct)
        s.expunge(acct)
    return acct


def _denied_request(app_, factory, peer: str, headers: dict[str, str]) -> uuid.UUID:
    """A PATIENT reads another patient's attachment: 403 and an AUTHZ_DENIED row."""
    actor = MagicMock(spec=Account)
    actor.id = uuid.uuid4()
    actor.user_type = UserType.PATIENT
    actor.status = AccountStatus.ACTIVE
    attachment = Attachment(
        id=uuid.uuid4(),
        clinical_entry_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        filename="a.pdf",
        content_type="application/pdf",
        size=8,
        storage_key="attachments/a.pdf",
        checksum=hashlib.sha256(b"x").hexdigest(),
    )

    def _dep(db: Session = Depends(get_db)) -> AttachmentService:
        audit = AuditService(AuditRepository(db))
        repo = MagicMock()
        repo.get.return_value = attachment
        return AttachmentService(
            repo, MagicMock(), audit, AuthorizationService(MagicMock(), audit), MagicMock()
        )

    app_.dependency_overrides[get_current_user] = lambda: actor
    app_.dependency_overrides[_get_attachment_service] = _dep
    resp = _client(app_, peer).get(f"/api/v1/attachments/{attachment.id}", headers=headers)
    assert resp.status_code == 403
    return actor.id


def test_authz_denied_row_records_client_address_through_trusted_peer(app_, factory) -> None:
    # SR-023 AC 6
    actor_id = _denied_request(app_, factory, PROXY, {"X-Forwarded-For": CLIENT})
    rows = _rows(factory, actor_id=actor_id, action=AuditAction.AUTHZ_DENIED)
    assert [r.ip for r in rows] == [CLIENT]


def test_forged_header_from_untrusted_peer_does_not_reach_the_row(app_, factory) -> None:
    # SR-042 AC 2
    actor_id = _denied_request(app_, factory, UNTRUSTED, {"X-Forwarded-For": FORGED})
    rows = _rows(factory, actor_id=actor_id, action=AuditAction.AUTHZ_DENIED)
    assert [r.ip for r in rows] == [UNTRUSTED]


def test_consent_grant_row_records_client_address(app_, factory) -> None:
    # SR-023 AC 6
    patient = _make_account(factory, UserType.PATIENT)
    doctor = _make_account(factory, UserType.DOCTOR)
    app_.dependency_overrides[get_current_user] = lambda: patient
    client = _client(app_, PROXY)
    client.cookies.set("medhub_csrf", "t")

    resp = client.post(
        "/api/v1/consents",
        json={"doctorId": str(doctor.id), "source": "MANUAL"},
        headers={"X-Forwarded-For": CLIENT, "X-CSRF-Token": "t"},
    )

    assert resp.status_code == 201, resp.text
    rows = _rows(factory, actor_id=patient.id, action=AuditAction.CONSENT_GRANTED)
    assert [r.ip for r in rows] == [CLIENT]


def test_login_failure_row_records_client_address_not_the_proxy(app_, factory) -> None:
    # SR-023 AC 6
    resp = _client(app_, PROXY).post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "Correct-Horse-Battery-9!"},
        headers={"X-Forwarded-For": CLIENT},
    )

    assert resp.status_code == 401
    rows = _rows(factory, action=AuditAction.LOGIN_FAILURE)
    assert [r.ip for r in rows] == [CLIENT]
