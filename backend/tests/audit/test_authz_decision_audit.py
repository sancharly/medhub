"""TC-009.10 (real DB): appointment and module authorization decisions are audited.

Requests go through ``create_app()`` with the real ``get_db`` against a PostgreSQL container
(SR-023 AC 7: actor, action, target, outcome, time and address on every decision, allowed or
denied; SR-005 AC 3; SR-011 AC 4; TASK-187). The proxy is trusted through ``TRUSTED_PROXIES``.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import fakeredis
import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

import app.db.models  # noqa: F401 — register all models
from app.api.deps import get_current_user, get_redis
from app.api.errors import ValidationProblem
from app.audit.actions import AuditAction
from app.auth.password import PasswordService
from app.authz.module_guard import ModuleAccessGuard
from app.core.config import get_settings
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.appointment import Appointment, AppointmentState
from app.db.models.audit import AuditLog, AuditOutcome
from app.db.models.base import Base
from app.main import create_app
from app.modules.router_registry import RouterRegistry

PROXY = "10.0.0.2"
CLIENT = "203.0.113.7"
HEADERS = {"X-Forwarded-For": CLIENT}


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
        s.execute(delete(Appointment))
        s.execute(delete(Account))
        s.commit()


@pytest.fixture
def app_(factory):
    application = create_app()
    redis = fakeredis.FakeRedis()
    application.dependency_overrides[get_redis] = lambda: redis
    probe = APIRouter()

    @probe.get("/ping")
    def ping() -> dict:
        return {"pong": True}

    @probe.get("/fail")
    def fail() -> dict:
        raise ValidationProblem("handler refuses")

    RouterRegistry(application).mount("probe", probe)
    return application


def _client(application) -> TestClient:
    return TestClient(application, raise_server_exceptions=False, client=(PROXY, 5000))


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


def _make_appointment(factory, doctor: Account, patient: Account) -> Appointment:
    appt = Appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        scheduled_at=datetime.now(UTC) + timedelta(days=1),
        state=AppointmentState.PENDING,
    )
    with factory() as s:
        s.add(appt)
        s.commit()
        s.refresh(appt)
        s.expunge(appt)
    return appt


def _rows(factory, **filters) -> list[AuditLog]:
    with factory() as check:
        stmt = select(AuditLog)
        for col, val in filters.items():
            stmt = stmt.where(getattr(AuditLog, col) == val)
        return list(check.execute(stmt).scalars().all())


def _assert_full_row(
    row: AuditLog,
    actor_id: uuid.UUID,
    action: str,
    target_type: str,
    target_id: str,
    outcome: AuditOutcome,
) -> None:
    assert row.actor_id == actor_id
    assert row.action == action
    assert row.target_type == target_type
    assert row.target_id == target_id
    assert row.outcome == outcome
    assert row.timestamp is not None
    assert row.ip == CLIENT


def test_allowed_appointment_list_writes_one_row(app_, factory) -> None:
    # SR-023 AC 7, SR-005 AC 3
    patient = _make_account(factory, UserType.PATIENT)
    app_.dependency_overrides[get_current_user] = lambda: patient

    resp = _client(app_).get("/api/v1/appointments", headers=HEADERS)

    assert resp.status_code == 200
    rows = _rows(factory, actor_id=patient.id)
    assert len(rows) == 1
    _assert_full_row(
        rows[0], patient.id, AuditAction.AUTHZ_ALLOWED, "appointment", "", AuditOutcome.SUCCESS
    )


def test_denied_appointment_list_writes_one_row(app_, factory) -> None:
    # SR-023 AC 7: an actor with no role is denied the list and the denial is recorded
    actor = MagicMock(spec=Account)
    actor.id = uuid.uuid4()
    actor.user_type = "GUEST"
    actor.status = AccountStatus.ACTIVE
    app_.dependency_overrides[get_current_user] = lambda: actor

    resp = _client(app_).get("/api/v1/appointments", headers=HEADERS)

    assert resp.status_code == 403
    rows = _rows(factory, actor_id=actor.id)
    assert len(rows) == 1
    _assert_full_row(
        rows[0], actor.id, AuditAction.AUTHZ_DENIED, "appointment", "", AuditOutcome.FAILURE
    )


def test_allowed_single_read_writes_one_row(app_, factory) -> None:
    # SR-023 AC 7
    doctor = _make_account(factory, UserType.DOCTOR)
    patient = _make_account(factory, UserType.PATIENT)
    appt = _make_appointment(factory, doctor, patient)
    app_.dependency_overrides[get_current_user] = lambda: patient

    resp = _client(app_).get(f"/api/v1/appointments/{appt.id}", headers=HEADERS)

    assert resp.status_code == 200
    rows = _rows(factory, actor_id=patient.id)
    assert len(rows) == 1
    _assert_full_row(
        rows[0],
        patient.id,
        AuditAction.AUTHZ_ALLOWED,
        "appointment",
        str(appt.id),
        AuditOutcome.SUCCESS,
    )


def test_denied_single_read_is_404_and_writes_denied_row(app_, factory) -> None:
    # SR-011 AC 4 (404 to the client) and SR-023 AC 7 (AUTHZ_DENIED row with address)
    doctor = _make_account(factory, UserType.DOCTOR)
    patient = _make_account(factory, UserType.PATIENT)
    stranger = _make_account(factory, UserType.PATIENT)
    appt = _make_appointment(factory, doctor, patient)
    app_.dependency_overrides[get_current_user] = lambda: stranger

    resp = _client(app_).get(f"/api/v1/appointments/{appt.id}", headers=HEADERS)

    assert resp.status_code == 404
    rows = _rows(factory, actor_id=stranger.id)
    assert len(rows) == 1
    _assert_full_row(
        rows[0],
        stranger.id,
        AuditAction.AUTHZ_DENIED,
        "appointment",
        str(appt.id),
        AuditOutcome.FAILURE,
    )


@pytest.mark.parametrize("enabled", [True, False])
def test_module_access_decision_writes_one_row(app_, factory, enabled: bool) -> None:
    # SR-023 AC 7, SR-015: the guard result is the input, the decision is audited
    doctor = _make_account(factory, UserType.DOCTOR)
    app_.dependency_overrides[get_current_user] = lambda: doctor

    with patch.object(ModuleAccessGuard, "is_module_enabled", return_value=enabled):
        resp = _client(app_).get("/api/v1/modules/probe/ping", headers=HEADERS)

    assert resp.status_code == (200 if enabled else 403)
    rows = _rows(factory, actor_id=doctor.id)
    assert len(rows) == 1
    if enabled:
        _assert_full_row(
            rows[0], doctor.id, AuditAction.AUTHZ_ALLOWED, "module", "probe", AuditOutcome.SUCCESS
        )
    else:
        _assert_full_row(
            rows[0], doctor.id, AuditAction.AUTHZ_DENIED, "module", "probe", AuditOutcome.FAILURE
        )


def test_allowed_row_is_lost_when_the_handler_then_fails_prb_060(app_, factory) -> None:
    """Documents PRB-060 (known limitation, not a requirement).

    An AUTHZ_ALLOWED row joins the request transaction (ADR-0016); when the handler then fails,
    ``get_db`` rolls it back, so the allowed decision of a request that ends in an error leaves no
    row. When PRB-060 is fixed this test flips on purpose: expect one AUTHZ_ALLOWED row.
    """
    doctor = _make_account(factory, UserType.DOCTOR)
    app_.dependency_overrides[get_current_user] = lambda: doctor

    with patch.object(ModuleAccessGuard, "is_module_enabled", return_value=True):
        resp = _client(app_).get("/api/v1/modules/probe/fail", headers=HEADERS)

    assert resp.status_code == 400
    assert _rows(factory, actor_id=doctor.id) == []
