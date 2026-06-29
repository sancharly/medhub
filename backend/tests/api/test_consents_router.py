"""Tests for consent endpoints (TASK-064)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.authz.consent import ConsentGrantResult
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.consent import ConsentSourceType
from app.db.repositories.session import get_db
from app.main import create_app


def _make_account(user_type: UserType = UserType.PATIENT) -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.email = "patient@example.com"
    acct.user_type = user_type
    acct.status = AccountStatus.ACTIVE
    return acct


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


def _make_grant_result(patient_id: uuid.UUID, doctor_id: uuid.UUID) -> ConsentGrantResult:
    return ConsentGrantResult(
        id=uuid.uuid4(),
        patient_id=patient_id,
        doctor_id=doctor_id,
        source_type=ConsentSourceType.MANUAL,
        appointment_id=None,
        active=True,
    )


class TestGrantConsent:
    def test_grant_consent_returns_201(self, client):
        actor = _make_account(UserType.PATIENT)
        doctor_id = uuid.uuid4()
        grant = _make_grant_result(actor.id, doctor_id)
        _auth_as(client, actor)

        with patch("app.authz.consent.ConsentService.grant", return_value=grant):
            resp = client.post(
                "/api/v1/consents",
                json={"doctorId": str(doctor_id)},
                cookies={"medhub_csrf": "tok"},
                headers={"X-CSRF-Token": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 201
        data = resp.json()
        assert data["active"] is True
        assert data["sourceType"] == "MANUAL"

    def test_grant_consent_requires_patient_role(self, client):
        """Doctors cannot grant consent on behalf of a patient (SR-008)."""
        actor = _make_account(UserType.DOCTOR)
        _auth_as(client, actor)

        resp = client.post(
            "/api/v1/consents",
            json={"doctorId": str(uuid.uuid4())},
            cookies={"medhub_csrf": "tok"},
            headers={"X-CSRF-Token": "tok"},
        )

        client.app.dependency_overrides = {}
        assert resp.status_code == 403

    def test_grant_consent_requires_auth(self, client):
        resp = client.post(
            "/api/v1/consents",
            json={"doctorId": str(uuid.uuid4())},
        )
        assert resp.status_code == 403


class TestRevokeConsent:
    def test_revoke_consent_returns_204(self, client):
        actor = _make_account(UserType.PATIENT)
        grant_id = uuid.uuid4()
        _auth_as(client, actor)

        # Create a mock grant owned by the actor
        mock_grant = MagicMock()
        mock_grant.patient_id = actor.id

        with (
            patch("app.authz.consent.ConsentService.revoke"),
            patch("app.db.repositories.base.Repository.get", return_value=mock_grant),
        ):
            resp = client.delete(
                f"/api/v1/consents/{grant_id}",
                cookies={"medhub_csrf": "tok"},
                headers={"X-CSRF-Token": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 204

    def test_revoke_consent_wrong_owner_returns_404(self, client):
        """Revoking another patient's grant returns 404 (SR-008, no enumeration)."""
        actor = _make_account(UserType.PATIENT)
        grant_id = uuid.uuid4()
        _auth_as(client, actor)

        other_patient_id = uuid.uuid4()
        mock_grant = MagicMock()
        mock_grant.patient_id = other_patient_id  # different patient

        with patch("app.db.repositories.base.Repository.get", return_value=mock_grant):
            resp = client.delete(
                f"/api/v1/consents/{grant_id}",
                cookies={"medhub_csrf": "tok"},
                headers={"X-CSRF-Token": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 404

    def test_revoke_consent_requires_auth(self, client):
        resp = client.delete(f"/api/v1/consents/{uuid.uuid4()}")
        assert resp.status_code == 403


class TestListMyConsents:
    def test_list_consents_returns_200(self, client):
        actor = _make_account(UserType.PATIENT)
        grant = _make_grant_result(actor.id, uuid.uuid4())
        _auth_as(client, actor)

        with patch("app.authz.consent.ConsentService.list_grants", return_value=[grant]):
            resp = client.get("/api/v1/me/consents")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1

    def test_list_consents_requires_auth(self, client):
        resp = client.get("/api/v1/me/consents")
        assert resp.status_code == 401
