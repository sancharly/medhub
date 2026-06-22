"""Tests for appointments endpoints (TASK-065)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.appointment import Appointment, AppointmentState
from app.db.repositories.session import get_db
from app.main import create_app


def _make_account(user_type: UserType = UserType.DOCTOR) -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.email = "doctor@example.com"
    acct.user_type = user_type
    acct.status = AccountStatus.ACTIVE
    return acct


def _make_appointment() -> Appointment:
    appt = MagicMock(spec=Appointment)
    appt.id = uuid.uuid4()
    appt.doctor_id = uuid.uuid4()
    appt.patient_id = uuid.uuid4()
    appt.scheduled_at = datetime.now(UTC) + timedelta(days=1)
    appt.state = AppointmentState.PENDING
    appt.created_at = datetime.now(UTC)
    return appt


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


def _auth_as(client, actor: Account) -> None:
    client.app.dependency_overrides[get_current_user] = lambda: actor

    def override_db():
        yield MagicMock()

    client.app.dependency_overrides[get_db] = override_db


class TestCreateAppointment:
    def test_create_appointment_returns_201(self, client):
        actor = _make_account(UserType.DOCTOR)
        appt = _make_appointment()
        _auth_as(client, actor)

        with patch("app.appointments.service.AppointmentService.create", return_value=appt):
            resp = client.post(
                "/api/v1/appointments",
                json={
                    "doctorId": str(appt.doctor_id),
                    "patientId": str(appt.patient_id),
                    "scheduledAt": appt.scheduled_at.isoformat(),
                },
                cookies={"medhub_csrf": "tok"},
                headers={"X-CSRF-Token": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 201

    def test_create_appointment_requires_auth(self, client):
        resp = client.post(
            "/api/v1/appointments",
            json={
                "doctorId": str(uuid.uuid4()),
                "patientId": str(uuid.uuid4()),
                "scheduledAt": datetime.now(UTC).isoformat(),
            },
        )
        assert resp.status_code == 401


class TestListAppointments:
    def test_list_appointments_returns_200(self, client):
        actor = _make_account(UserType.DOCTOR)
        appt = _make_appointment()
        _auth_as(client, actor)

        with patch("app.appointments.service.AppointmentService.list_for", return_value=[appt]):
            resp = client.get("/api/v1/appointments")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestConfirmAppointment:
    def test_confirm_appointment_returns_200(self, client):
        actor = _make_account(UserType.PATIENT)
        appt = _make_appointment()
        appt.state = AppointmentState.CONFIRMED
        _auth_as(client, actor)

        with patch("app.appointments.service.AppointmentService.confirm", return_value=appt):
            resp = client.post(
                f"/api/v1/appointments/{appt.id}/confirm",
                cookies={"medhub_csrf": "tok"},
                headers={"X-CSRF-Token": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 200


class TestDeclineAppointment:
    def test_decline_appointment_returns_200(self, client):
        actor = _make_account(UserType.PATIENT)
        appt = _make_appointment()
        appt.state = AppointmentState.DECLINED
        _auth_as(client, actor)

        with patch("app.appointments.service.AppointmentService.decline", return_value=appt):
            resp = client.post(
                f"/api/v1/appointments/{appt.id}/decline",
                cookies={"medhub_csrf": "tok"},
                headers={"X-CSRF-Token": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
