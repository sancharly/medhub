"""Tests for lifecycle endpoints (TASK-062)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.models.account import Account, AccountStatus, UserType
from app.db.repositories.session import get_db
from app.main import create_app


def _make_account(user_type: UserType = UserType.SYSADMIN) -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.email = "admin@example.com"
    acct.user_type = user_type
    acct.status = AccountStatus.ACTIVE
    acct.first_name = "Admin"
    acct.surname = "User"
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


class TestDeactivateEndpoint:
    def test_deactivate_returns_204(self, client):
        actor = _make_account(UserType.SYSADMIN)
        target_id = uuid.uuid4()
        _auth_as(client, actor)

        with patch("app.identity.lifecycle.LifecycleService.deactivate"):
            resp = client.post(
                f"/api/v1/accounts/{target_id}/deactivate",
                cookies={"medhub_csrf": "tok"},
                headers={"X-CSRF-Token": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 204

    def test_deactivate_requires_auth(self, client):
        resp = client.post(f"/api/v1/accounts/{uuid.uuid4()}/deactivate")
        assert resp.status_code == 401


class TestReactivateEndpoint:
    def test_reactivate_returns_204(self, client):
        actor = _make_account(UserType.SYSADMIN)
        target_id = uuid.uuid4()
        _auth_as(client, actor)

        with patch("app.identity.lifecycle.LifecycleService.reactivate"):
            resp = client.post(
                f"/api/v1/accounts/{target_id}/reactivate",
                cookies={"medhub_csrf": "tok"},
                headers={"X-CSRF-Token": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 204

    def test_reactivate_requires_auth(self, client):
        resp = client.post(f"/api/v1/accounts/{uuid.uuid4()}/reactivate")
        assert resp.status_code == 401


class TestDeleteEndpoint:
    def test_delete_returns_200(self, client):
        import json as _json

        from app.identity.erasure import ErasureResult

        actor = _make_account(UserType.SYSADMIN)
        target_id = uuid.uuid4()
        dataset_id = uuid.uuid4()
        _auth_as(client, actor)

        # Target account that matches the confirmation body
        target = _make_account(UserType.PATIENT)
        target.id = target_id
        target.email = "patient@example.com"

        erasure_result = ErasureResult(dataset_id=dataset_id, retrieval_code="raw-code")

        with patch("app.identity.erasure.ErasureService.delete", return_value=erasure_result), \
             patch("app.db.repositories.account_repo.AccountRepository.get_by_id", return_value=target):
            resp = client.request(
                "DELETE",
                f"/api/v1/accounts/{target_id}",
                content=_json.dumps({
                    "confirmEmail": "patient@example.com",
                    "confirmAccountType": "PATIENT",
                }),
                headers={
                    "Content-Type": "application/json",
                    "X-CSRF-Token": "tok",
                },
                cookies={"medhub_csrf": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        data = resp.json()
        assert data["datasetId"] == str(dataset_id)

    def test_delete_confirmation_mismatch_returns_400(self, client):
        """Wrong email in confirmation body → 400 (SR-034.6)."""
        import json as _json

        actor = _make_account(UserType.SYSADMIN)
        target_id = uuid.uuid4()
        _auth_as(client, actor)

        target = _make_account(UserType.PATIENT)
        target.id = target_id
        target.email = "real@example.com"

        with patch("app.db.repositories.account_repo.AccountRepository.get_by_id", return_value=target):
            resp = client.request(
                "DELETE",
                f"/api/v1/accounts/{target_id}",
                content=_json.dumps({
                    "confirmEmail": "wrong@example.com",
                    "confirmAccountType": "PATIENT",
                }),
                headers={
                    "Content-Type": "application/json",
                    "X-CSRF-Token": "tok",
                },
                cookies={"medhub_csrf": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 400

    def test_delete_requires_auth(self, client):
        import json as _json

        resp = client.request(
            "DELETE",
            f"/api/v1/accounts/{uuid.uuid4()}",
            content=_json.dumps({
                "confirmEmail": "x@example.com",
                "confirmAccountType": "PATIENT",
            }),
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 401
