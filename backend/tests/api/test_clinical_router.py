"""Tests for clinical entry endpoints (TASK-066, TASK-044a)."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.clinical import ClinicalEntry
from app.db.repositories.session import get_db
from app.main import create_app


def _make_account(user_type: UserType = UserType.DOCTOR) -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.email = "doctor@example.com"
    acct.user_type = user_type
    acct.status = AccountStatus.ACTIVE
    return acct


def _make_entry(patient_id: uuid.UUID, doctor_id: uuid.UUID) -> ClinicalEntry:
    entry = MagicMock(spec=ClinicalEntry)
    entry.id = uuid.uuid4()
    entry.patient_id = patient_id
    entry.author_doctor_id = doctor_id
    entry.occurred_at = datetime.now(UTC)
    entry.description = "Test entry"
    entry.created_at = datetime.now(UTC)
    return entry


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


class TestListClinicalEntries:
    def test_list_entries_returns_200(self, client):
        actor = _make_account(UserType.DOCTOR)
        patient_id = uuid.uuid4()
        entry = _make_entry(patient_id, actor.id)
        _auth_as(client, actor)

        with patch("app.clinical.service.ClinicalDataService.list_entries", return_value=[entry]):
            resp = client.get(f"/api/v1/patients/{patient_id}/clinical-entries")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_entries_requires_auth(self, client):
        resp = client.get(f"/api/v1/patients/{uuid.uuid4()}/clinical-entries")
        assert resp.status_code == 401


class TestCreateClinicalEntry:
    def test_create_entry_returns_201(self, client):
        actor = _make_account(UserType.DOCTOR)
        patient_id = uuid.uuid4()
        entry = _make_entry(patient_id, actor.id)
        _auth_as(client, actor)

        with patch("app.clinical.service.ClinicalDataService.create_entry", return_value=entry):
            resp = client.post(
                f"/api/v1/patients/{patient_id}/clinical-entries",
                json={
                    "occurredAt": datetime.now(UTC).isoformat(),
                    "description": "Routine check-up",
                },
                cookies={"medhub_csrf": "tok"},
                headers={"X-CSRF-Token": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 201

    def test_create_entry_requires_auth(self, client):
        resp = client.post(
            f"/api/v1/patients/{uuid.uuid4()}/clinical-entries",
            json={"occurredAt": datetime.now(UTC).isoformat(), "description": "Test"},
        )
        assert resp.status_code == 401


def _make_patient_account() -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.email = "patient@example.com"
    acct.first_name = "Jane"
    acct.surname = "Doe"
    acct.date_of_birth = date(1990, 1, 1)
    acct.user_type = UserType.PATIENT
    acct.status = AccountStatus.ACTIVE
    return acct


class TestListAccessiblePatients:
    def test_doctor_with_consents_returns_patients(self, client):
        actor = _make_account(UserType.DOCTOR)
        patient = _make_patient_account()
        _auth_as(client, actor)

        with patch(
            "app.clinical.service.ClinicalDataService.list_accessible_patients",
            return_value=[patient],
        ):
            resp = client.get("/api/v1/clinical-entries/patients")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == str(patient.id)

    def test_doctor_with_no_consents_returns_empty_list(self, client):
        actor = _make_account(UserType.DOCTOR)
        _auth_as(client, actor)

        with patch(
            "app.clinical.service.ClinicalDataService.list_accessible_patients",
            return_value=[],
        ):
            resp = client.get("/api/v1/clinical-entries/patients")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        assert resp.json() == []

    def test_patient_calling_endpoint_returns_403(self, client):
        actor = _make_account(UserType.PATIENT)
        _auth_as(client, actor)

        resp = client.get("/api/v1/clinical-entries/patients")

        client.app.dependency_overrides = {}
        assert resp.status_code == 403

    def test_admin_calling_endpoint_returns_403(self, client):
        actor = _make_account(UserType.ADMIN)
        _auth_as(client, actor)

        resp = client.get("/api/v1/clinical-entries/patients")

        client.app.dependency_overrides = {}
        assert resp.status_code == 403

    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/api/v1/clinical-entries/patients")
        assert resp.status_code == 401
