"""Integration tests for admin projection wiring (TASK-029a).

Verifies that ADMIN users get projected (non-PII) account responses while
SYSADMIN gets full AccountResponse.
"""

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
    acct.email = "user@example.com"
    acct.user_type = user_type
    acct.status = status
    acct.first_name = "Alice"
    acct.surname = "Smith"
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
    client.app.dependency_overrides[get_current_user] = lambda: actor

    def override_db():
        yield MagicMock()

    client.app.dependency_overrides[get_db] = override_db


class TestAdminProjectionOnListAccounts:
    def test_admin_gets_projected_shape(self, client):
        """ADMIN listing accounts receives AdminAccountListResponse (no email, no credentials)."""
        actor = _make_account(UserType.ADMIN)
        target = _make_account(UserType.PATIENT)
        _auth_as(client, actor)

        with (
            patch("app.db.repositories.account_repo.AccountRepository.list", return_value=[target]),
            patch("app.authz.service.AuthorizationService.authorize"),
        ):
            resp = client.get("/api/v1/accounts")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        item = data["items"][0]
        # Projected shape has accountType, not userType; no email
        assert "accountType" in item
        assert "email" not in item
        assert "passwordHash" not in item

    def test_sysadmin_gets_full_account_response(self, client):
        """SYSADMIN listing accounts receives full AccountResponse including email."""
        actor = _make_account(UserType.SYSADMIN)
        target = _make_account(UserType.PATIENT)
        _auth_as(client, actor)

        with (
            patch("app.db.repositories.account_repo.AccountRepository.list", return_value=[target]),
            patch("app.authz.service.AuthorizationService.authorize"),
        ):
            resp = client.get("/api/v1/accounts")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        data = resp.json()
        item = data["items"][0]
        assert "email" in item
        assert "userType" in item


class TestAdminProjectionOnGetAccount:
    def test_admin_gets_projected_account(self, client):
        """ADMIN fetching a single account receives AdminAccountResponse."""
        actor = _make_account(UserType.ADMIN)
        target = _make_account(UserType.PATIENT)
        _auth_as(client, actor)

        with patch("app.identity.account_service.AccountService.get_profile", return_value=target):
            resp = client.get(f"/api/v1/accounts/{target.id}")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        data = resp.json()
        assert "accountType" in data
        assert "email" not in data
        assert "passwordHash" not in data

    def test_sysadmin_gets_full_account(self, client):
        """SYSADMIN fetching a single account receives full AccountResponse."""
        actor = _make_account(UserType.SYSADMIN)
        target = _make_account(UserType.DOCTOR)
        _auth_as(client, actor)

        with patch("app.identity.account_service.AccountService.get_profile", return_value=target):
            resp = client.get(f"/api/v1/accounts/{target.id}")

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        data = resp.json()
        assert "email" in data
        assert "userType" in data
