"""Tests for activation endpoints (TASK-061)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.models.account import Account, AccountStatus, UserType
from app.main import create_app


def _make_account(status: AccountStatus = AccountStatus.INACTIVE) -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.email = "user@example.com"
    acct.user_type = UserType.PATIENT
    acct.status = status
    acct.activation_token_hash = "abc123"
    acct.activation_token_expires_at = datetime.now(UTC) + timedelta(hours=24)
    return acct


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


class TestValidateToken:
    def test_valid_token_returns_valid_true(self, client):
        account = _make_account()
        token_hash = __import__("hashlib").sha256(b"valid-token").hexdigest()
        account.activation_token_hash = token_hash

        with patch("app.db.repositories.account_repo.AccountRepository.list", return_value=[account]):
            resp = client.get("/api/v1/activation/valid-token")

        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["accountId"] == str(account.id)

    def test_unknown_token_returns_valid_false(self, client):
        with patch("app.db.repositories.account_repo.AccountRepository.list", return_value=[]):
            resp = client.get("/api/v1/activation/unknown-token")

        assert resp.status_code == 200
        assert resp.json()["valid"] is False

    def test_expired_token_returns_valid_false(self, client):
        account = _make_account()
        token_hash = __import__("hashlib").sha256(b"expired-token").hexdigest()
        account.activation_token_hash = token_hash
        account.activation_token_expires_at = datetime.now(UTC) - timedelta(hours=1)

        with patch("app.db.repositories.account_repo.AccountRepository.list", return_value=[account]):
            resp = client.get("/api/v1/activation/expired-token")

        assert resp.status_code == 200
        assert resp.json()["valid"] is False


class TestActivateAccount:
    def test_activate_returns_204(self, client):
        account_id = uuid.uuid4()
        with patch("app.identity.activation.ActivationService.activate", return_value=MagicMock()):
            resp = client.post(
                "/api/v1/activation/valid-token",
                json={"accountId": str(account_id), "password": "NewPassword123!"},
            )

        assert resp.status_code == 204

    def test_activate_invalid_token_returns_401(self, client):
        from app.api.errors import UnauthenticatedError

        account_id = uuid.uuid4()
        with patch(
            "app.identity.activation.ActivationService.activate",
            side_effect=UnauthenticatedError("Invalid or expired activation token."),
        ):
            resp = client.post(
                "/api/v1/activation/bad-token",
                json={"accountId": str(account_id), "password": "NewPassword123!"},
            )

        assert resp.status_code == 401
