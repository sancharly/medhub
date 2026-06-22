"""Tests for accounts endpoints (TASK-061)."""

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


def _make_account(
    user_type: UserType = UserType.SYSADMIN,
    status: AccountStatus = AccountStatus.ACTIVE,
) -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.email = "admin@example.com"
    acct.user_type = user_type
    acct.status = status
    acct.first_name = "Admin"
    acct.surname = "User"
    acct.date_of_birth = None
    acct.password_hash = None
    acct.password_changed_at = None
    acct.created_at = datetime.now(UTC)
    return acct


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


def _auth_as(client, actor: Account) -> None:
    """Override get_current_user to return actor directly."""
    client.app.dependency_overrides[get_current_user] = lambda: actor

    def override_db():
        yield MagicMock()

    client.app.dependency_overrides[get_db] = override_db


class TestCreateAccount:
    def test_create_account_returns_201(self, client):
        actor = _make_account(UserType.SYSADMIN)
        new_account = _make_account(UserType.DOCTOR)
        _auth_as(client, actor)

        with patch("app.identity.account_service.AccountService.create", return_value=new_account):
            resp = client.post(
                "/api/v1/accounts",
                json={"email": "doctor@example.com", "userType": "DOCTOR"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 201
        assert "id" in resp.json()

    def test_create_account_requires_auth(self, client):
        resp = client.post(
            "/api/v1/accounts",
            json={"email": "doctor@example.com", "userType": "DOCTOR"},
        )
        assert resp.status_code == 401

    def test_create_account_missing_email_returns_error(self, client):
        actor = _make_account(UserType.SYSADMIN)
        _auth_as(client, actor)

        resp = client.post("/api/v1/accounts", json={"userType": "DOCTOR"})

        client.app.dependency_overrides = {}
        assert resp.status_code in (400, 422)


class TestListAccounts:
    def test_list_accounts_returns_200(self, client):
        actor = _make_account(UserType.SYSADMIN)
        _auth_as(client, actor)

        with (
            patch("app.db.repositories.account_repo.AccountRepository.list", return_value=[actor]),
            patch("app.authz.service.AuthorizationService.authorize"),
        ):
            resp = client.get("/api/v1/accounts")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_list_accounts_requires_auth(self, client):
        resp = client.get("/api/v1/accounts")
        assert resp.status_code == 401


class TestGetAccount:
    def test_get_account_returns_200(self, client):
        actor = _make_account(UserType.SYSADMIN)
        target = _make_account(UserType.DOCTOR)
        _auth_as(client, actor)

        with patch("app.identity.account_service.AccountService.get_profile", return_value=target):
            resp = client.get(f"/api/v1/accounts/{target.id}")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200

    def test_get_account_requires_auth(self, client):
        resp = client.get(f"/api/v1/accounts/{uuid.uuid4()}")
        assert resp.status_code == 401
