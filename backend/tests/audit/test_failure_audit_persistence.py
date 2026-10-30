"""TC-009.4..8 (real DB): failure and refusal audit events survive the error response.

Each test sends the request through ``create_app()`` with the real ``get_db`` (rolls back on any
exception) against a PostgreSQL container, receives the error status, then looks for the row on a
separate session (PRB-052, SR-023 AC 1 and AC 2, ADR-0016). Independent rows commit outside any
test transaction, so every test deletes the ``audit_log`` and ``account`` rows it created.
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
from app.api.errors import AuthorizationError
from app.api.routers.attachments import _get_attachment_service
from app.attachments.service import AttachmentService
from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.auth.password import PasswordService
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.attachment import Attachment
from app.db.models.audit import AuditLog, AuditOutcome
from app.db.models.base import Base
from app.db.models.group import Group
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.session import get_db
from app.main import create_app

_PASSWORD = "Correct-Horse-Battery-9!"


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
    maker = sessionmaker(bind=pg_engine)
    yield maker
    with maker() as s:
        s.execute(delete(AuditLog))
        s.execute(delete(Account))
        s.execute(delete(Group))
        s.commit()


@pytest.fixture
def app_(factory):
    application = create_app()
    redis = fakeredis.FakeRedis()
    application.dependency_overrides[get_redis] = lambda: redis
    return application


def _client(application) -> TestClient:
    return TestClient(application, raise_server_exceptions=False)


def _rows(factory, **filters) -> list[AuditLog]:
    with factory() as check:
        stmt = select(AuditLog)
        for col, val in filters.items():
            stmt = stmt.where(getattr(AuditLog, col) == val)
        return list(check.execute(stmt).scalars().all())


def _make_account(
    factory,
    *,
    status: AccountStatus = AccountStatus.ACTIVE,
    user_type: UserType = UserType.DOCTOR,
    token: str | None = None,
) -> Account:
    acct = Account(
        email=f"{uuid.uuid4().hex}@example.com",
        password_hash=PasswordService().hash(_PASSWORD),
        user_type=user_type,
        status=status,
    )
    if token is not None:
        from datetime import UTC, datetime, timedelta  # noqa: PLC0415

        acct.activation_token_hash = hashlib.sha256(token.encode()).hexdigest()
        acct.activation_token_expires_at = datetime.now(UTC) + timedelta(hours=1)
    with factory() as s:
        s.add(acct)
        s.commit()
        s.refresh(acct)
        s.expunge(acct)
    return acct


# --- TC-009.4: AUTHZ_DENIED persists after 403 ---------------------------------------------


def test_authz_denied_persists_after_403(app_, factory) -> None:
    actor = MagicMock(spec=Account)
    actor.id = uuid.uuid4()
    actor.user_type = UserType.PATIENT
    actor.status = AccountStatus.ACTIVE
    other_patient = uuid.uuid4()
    attachment = Attachment(
        id=uuid.uuid4(),
        clinical_entry_id=uuid.uuid4(),
        patient_id=other_patient,
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

    resp = _client(app_).get(f"/api/v1/attachments/{attachment.id}")

    assert resp.status_code == 403
    rows = _rows(factory, actor_id=actor.id)
    assert [(r.action, r.outcome) for r in rows] == [
        (AuditAction.AUTHZ_DENIED, AuditOutcome.FAILURE)
    ]
    assert rows[0].target_id == str(other_patient)


# --- TC-009.5: LOGIN_FAILURE (3 branches) and ACCOUNT_LOCKOUT persist after 401 -------------


def _login(application, email: str, password: str):
    return _client(application).post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )


def test_login_failure_unknown_email_persists_after_401(app_, factory) -> None:
    resp = _login(app_, "nobody@example.com", _PASSWORD)

    assert resp.status_code == 401
    rows = _rows(factory, action=AuditAction.LOGIN_FAILURE)
    assert len(rows) == 1
    assert rows[0].outcome == AuditOutcome.FAILURE
    assert rows[0].actor_id is None


def test_login_failure_wrong_password_persists_after_401(app_, factory) -> None:
    acct = _make_account(factory)

    resp = _login(app_, acct.email, "wrong-password")

    assert resp.status_code == 401
    rows = _rows(factory, action=AuditAction.LOGIN_FAILURE)
    assert [(r.actor_id, r.outcome) for r in rows] == [(acct.id, AuditOutcome.FAILURE)]


def test_login_failure_inactive_account_persists_after_401(app_, factory) -> None:
    acct = _make_account(factory, status=AccountStatus.INACTIVE)

    resp = _login(app_, acct.email, _PASSWORD)

    assert resp.status_code == 401
    rows = _rows(factory, action=AuditAction.LOGIN_FAILURE)
    assert [(r.actor_id, r.outcome) for r in rows] == [(acct.id, AuditOutcome.FAILURE)]


def test_login_failure_locked_account_and_lockout_persist_after_401(app_, factory) -> None:
    acct = _make_account(factory)

    for _ in range(5):
        assert _login(app_, acct.email, "wrong-password").status_code == 401
    lockout = _rows(factory, action=AuditAction.ACCOUNT_LOCKOUT)
    assert [(r.target_id, r.outcome) for r in lockout] == [(str(acct.id), AuditOutcome.SUCCESS)]

    # Locked branch: even the correct password is refused and the refusal is recorded.
    assert _login(app_, acct.email, _PASSWORD).status_code == 401
    failures = _rows(factory, action=AuditAction.LOGIN_FAILURE)
    assert len(failures) == 6
    assert all(r.actor_id == acct.id and r.outcome == AuditOutcome.FAILURE for r in failures)


# --- TC-009.6: ACTIVATION_FAILED persists after 401 -----------------------------------------


def test_activation_failed_persists_after_401(app_, factory) -> None:
    acct = _make_account(factory, status=AccountStatus.INACTIVE, token="right-token")

    resp = _client(app_).post(
        "/api/v1/activation/wrong-token",
        json={"accountId": str(acct.id), "password": _PASSWORD, "confirmPassword": _PASSWORD},
    )

    assert resp.status_code == 401
    rows = _rows(factory, action=AuditAction.ACTIVATION_FAILED)
    assert [(r.target_id, r.outcome) for r in rows] == [(str(acct.id), AuditOutcome.FAILURE)]


# --- TC-009.8: atomicity ---------------------------------------------------------------------


def test_failure_row_persists_while_business_row_and_success_event_roll_back(app_, factory) -> None:
    group_name = f"atomic-{uuid.uuid4().hex}"
    actor = uuid.uuid4()

    @app_.get("/__test/atomicity")
    def _route(db: Session = Depends(get_db)) -> None:
        db.add(Group(name=group_name))
        db.flush()
        audit = AuditService(AuditRepository(db))
        audit.record(actor, AuditAction.AUTH_LOGIN, None, None, AuditOutcome.SUCCESS, None)
        audit.record(actor, AuditAction.AUTHZ_DENIED, "x", None, AuditOutcome.FAILURE, None)
        raise AuthorizationError("denied")

    resp = _client(app_).get("/__test/atomicity")

    assert resp.status_code == 403
    with factory() as check:
        assert check.execute(select(Group).where(Group.name == group_name)).first() is None
    rows = _rows(factory, actor_id=actor)
    assert [(r.action, r.outcome) for r in rows] == [
        (AuditAction.AUTHZ_DENIED, AuditOutcome.FAILURE)
    ]
