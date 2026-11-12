"""TC-009.12: no secret is stored in any audit field (SR-023 AC 5 and AC 9, TASK-192).

``AuditService.record`` accepts only closed shapes for ``action``, ``target_type`` and
``target_id`` and refuses anything else before a row is built (RISK-005, RISK-006). The unit cases
cover every secret kind of AC 9 under every field; the real-database cases show that nothing is
written on a refusal and that the audit rows of a realistic flow (login, logout, change password)
contain no session token, CSRF token, password or any configured secret.
"""

from __future__ import annotations

import base64
import os
import secrets
import uuid
from collections.abc import Iterator
from unittest.mock import MagicMock

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

import app.db.models  # noqa: F401 — register all models
from app.api.deps import get_redis
from app.audit.actions import AuditAction
from app.audit.service import _TARGETS, AuditFieldError, AuditService
from app.auth.password import PasswordService
from app.core.secret_settings import secret_values, settings_env
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.audit import AuditLog, AuditOutcome
from app.db.models.base import Base
from app.db.models.password_history import PasswordHistory
from app.db.repositories.audit_repo import AuditRepository
from app.main import create_app
from postgres_image import POSTGRES_IMAGE

_PASSWORD = "Correct-Horse-Battery-9!"
_NEW_PASSWORD = "Another-Staple-Horse-77!"

# SR-023 AC 9: every kind of value issued or received as a credential or secret.
_SECRETS = {
    "password": _PASSWORD,
    "session_token": secrets.token_urlsafe(32),
    "activation_token": secrets.token_urlsafe(32),
    "retrieval_code": secrets.token_urlsafe(32),  # ErasureService generator
    "base64_key": base64.urlsafe_b64encode(os.urandom(32)).decode(),
    "object_store_access_key": "AKIA" + secrets.token_hex(8).upper(),
}


def _record(service: AuditService, **fields) -> None:
    args = {
        "actor": uuid.uuid4(),
        "action": AuditAction.AUTH_LOGIN,
        "target_type": "account",
        "target_id": str(uuid.uuid4()),
        "outcome": AuditOutcome.SUCCESS,
        "ip": None,
    }
    args.update(fields)
    service.record(**args)


@pytest.fixture
def repo() -> MagicMock:
    return MagicMock(spec=AuditRepository)


@pytest.fixture
def service(repo) -> AuditService:
    return AuditService(repo)


def _placements(secret: str) -> list[dict]:
    return [
        {"action": secret},
        {"target_type": secret},
        {"target_id": secret},
        {"target_type": "group_module", "target_id": f"{uuid.uuid4()}:{secret}"},
        {"target_type": "group_membership", "target_id": f"{uuid.uuid4()}:{secret}"},
    ]


@pytest.mark.parametrize("kind", sorted(_SECRETS))
def test_secret_under_any_field_is_refused(service, repo, kind) -> None:
    # SR-023 AC 9
    for fields in _placements(_SECRETS[kind]):
        with pytest.raises(AuditFieldError) as exc:
            _record(service, **fields)
        assert _SECRETS[kind] not in str(exc.value)  # message names the field, never the value
    repo.add.assert_not_called()
    repo.add_independent.assert_not_called()


@pytest.mark.parametrize("target_type", sorted(_TARGETS))
@pytest.mark.parametrize("kind", sorted(_SECRETS))
def test_secret_as_target_id_is_refused_for_every_target_type(
    service, repo, kind, target_type
) -> None:
    # SR-023 AC 9: a secret arriving under an unexpected field/shape is refused, not stored.
    with pytest.raises(AuditFieldError):
        _record(service, target_type=target_type, target_id=_SECRETS[kind])
    repo.add.assert_not_called()


def test_secret_with_key_value_form_is_refused(service, repo) -> None:
    # SR-023 AC 9: the key=value form the old scrub caught is refused too.
    with pytest.raises(AuditFieldError):
        _record(service, target_type="account", target_id="token=" + _SECRETS["session_token"])
    repo.add.assert_not_called()


def test_target_id_without_target_type_is_refused(service, repo) -> None:
    # SR-023 AC 9: an identifier needs a known type to be checked against.
    with pytest.raises(AuditFieldError):
        _record(service, target_type=None, target_id=str(uuid.uuid4()))
    repo.add.assert_not_called()


def test_error_names_the_field_not_the_value(service) -> None:
    secret = _SECRETS["session_token"]
    with pytest.raises(AuditFieldError, match="target_id") as exc:
        _record(service, target_id=secret)
    assert secret not in str(exc.value)


# --- real database ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def pg_engine():
    with PostgresContainer(POSTGRES_IMAGE) as container:
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
        s.execute(delete(PasswordHistory))
        s.execute(delete(Account))
        s.commit()


def _row_count(factory) -> int:
    with factory() as s:
        return s.execute(select(func.count()).select_from(AuditLog)).scalar_one()


def test_refused_record_writes_no_row(factory) -> None:
    # SR-023 AC 9 (real database)
    with factory() as s:
        service = AuditService(AuditRepository(s))
        for secret in _SECRETS.values():
            for fields in _placements(secret):
                with pytest.raises(AuditFieldError):
                    _record(service, **fields)
                    s.flush()
        s.commit()
    assert _row_count(factory) == 0


def _audit_text(factory) -> list[str]:
    """Every column of every audit row, as text."""
    with factory() as s:
        rows = s.execute(select(AuditLog)).scalars().all()
        return [
            str(getattr(r, col.key))
            for r in rows
            for col in AuditLog.__table__.columns
            if getattr(r, col.key) is not None
        ]


def _leaked(cells: list[str], values: list[str]) -> list[str]:
    return [v for v in values if any(v in cell for cell in cells)]


def test_flow_scan_catches_a_configured_secret_written_into_an_audit_row(factory) -> None:
    # Negative control for the flow scan below (TASK-197): a row written around the service with
    # a configured secret in a free-text column must be found, for every configured secret.
    configured = secret_values(settings_env())
    assert len(configured) >= 4  # database password, at-rest key, object-store access and secret
    with factory() as s:
        for value in configured:
            s.add(
                AuditLog(
                    action="LOGIN_FAILURE",
                    outcome=AuditOutcome.FAILURE,
                    ip=value,
                )
            )
        s.commit()
    assert _leaked(_audit_text(factory), configured) == configured


def test_flow_rows_hold_no_session_token_and_logout_records_the_address(factory) -> None:
    # SR-023 AC 5 (real database): login, logout, change password write no credential, and the
    # logout row records the account and the client address instead of the session token.
    acct = Account(
        email=f"{uuid.uuid4().hex}@example.com",
        password_hash=PasswordService().hash(_PASSWORD),
        user_type=UserType.DOCTOR,
        status=AccountStatus.ACTIVE,
    )
    with factory() as s:
        s.add(acct)
        s.commit()
        s.refresh(acct)
        account_id = acct.id

    application = create_app()
    redis = fakeredis.FakeRedis()
    application.dependency_overrides[get_redis] = lambda: redis
    client = TestClient(application, raise_server_exceptions=False, client=("203.0.113.7", 5000))

    def _login():
        resp = client.post("/api/v1/auth/login", json={"email": acct.email, "password": _PASSWORD})
        assert resp.status_code == 200
        session = resp.cookies["medhub_session"]
        csrf = resp.cookies["medhub_csrf"]
        return (
            session,
            csrf,
            {"Cookie": f"medhub_session={session}; medhub_csrf={csrf}", "X-CSRF-Token": csrf},
        )

    session_a, csrf_a, headers_a = _login()
    session_b, csrf_b, headers_b = _login()
    resp = client.post(
        "/api/v1/auth/password",
        headers=headers_b,
        json={
            "current_password": _PASSWORD,
            "new_password": _NEW_PASSWORD,
            "confirm_new_password": _NEW_PASSWORD,
        },
    )
    assert resp.status_code == 204, resp.text
    resp = client.post("/api/v1/auth/logout", headers=headers_b)
    assert resp.status_code == 204, resp.text

    with factory() as s:
        logout = (
            s.execute(select(AuditLog).where(AuditLog.action == AuditAction.LOGOUT)).scalars().all()
        )
    assert len(logout) == 1
    assert logout[0].target_type == "account"
    assert logout[0].target_id == str(account_id)
    assert logout[0].ip == "203.0.113.7"
    with factory() as s:
        changed = (
            s.execute(select(AuditLog).where(AuditLog.action == AuditAction.PASSWORD_CHANGED))
            .scalars()
            .all()
        )
    assert len(changed) == 1 and changed[0].target_id == str(account_id)

    text = _audit_text(factory)
    assert text, "the flow wrote no audit rows"
    forbidden = [
        session_a,
        session_b,
        csrf_a,
        csrf_b,
        _PASSWORD,
        _NEW_PASSWORD,
        *secret_values(settings_env()),  # TASK-197: every configured secret, from one list
    ]
    assert _leaked(text, forbidden) == []
