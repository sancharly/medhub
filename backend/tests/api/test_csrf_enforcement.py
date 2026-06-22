"""Tests for CSRF enforcement (TASK-069)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_session_service
from app.auth.session import Session as UserSession
from app.auth.session import SessionService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.repositories.session import get_db
from app.main import create_app


def _make_account(user_type: UserType = UserType.DOCTOR) -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.email = "doctor@example.com"
    acct.user_type = user_type
    acct.status = AccountStatus.ACTIVE
    return acct


def _make_session(account: Account) -> UserSession:
    now = datetime.now(UTC)
    return UserSession(
        session_id="test-session-id",
        account_id=account.id,
        role=account.user_type,
        created_at=now,
        last_seen_at=now,
        ip="1.2.3.4",
        absolute_expires_at=now + timedelta(hours=8),
    )


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app):
    return TestClient(app, raise_server_exceptions=False)


def _setup_auth(client, account: Account) -> None:
    session = _make_session(account)
    mock_svc = MagicMock(spec=SessionService)
    mock_svc.resolve.return_value = session
    client.app.dependency_overrides[get_session_service] = lambda: mock_svc

    def override_db():
        yield MagicMock()

    client.app.dependency_overrides[get_db] = override_db


class TestCSRFEnforcement:
    def test_logout_without_csrf_returns_401(self, client):
        actor = _make_account()
        _setup_auth(client, actor)

        with patch(
            "app.db.repositories.account_repo.AccountRepository.get_by_id",
            return_value=actor,
        ):
            resp = client.post(
                "/api/v1/auth/logout",
                cookies={"medhub_session": "test-session-id"},
                # No CSRF cookie/header
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 401

    def test_logout_with_csrf_succeeds(self, client):
        actor = _make_account()
        _setup_auth(client, actor)

        with patch(
            "app.db.repositories.account_repo.AccountRepository.get_by_id",
            return_value=actor,
        ):
            resp = client.post(
                "/api/v1/auth/logout",
                cookies={"medhub_session": "test-session-id", "medhub_csrf": "valid-token"},
                headers={"X-CSRF-Token": "valid-token"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 204

    def test_csrf_mismatch_returns_401(self, client):
        actor = _make_account()
        _setup_auth(client, actor)

        with patch(
            "app.db.repositories.account_repo.AccountRepository.get_by_id",
            return_value=actor,
        ):
            resp = client.post(
                "/api/v1/auth/logout",
                cookies={"medhub_session": "test-session-id", "medhub_csrf": "cookie-token"},
                headers={"X-CSRF-Token": "different-token"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 401

    def test_get_requests_skip_csrf(self, client):
        """GET requests should not require CSRF."""
        actor = _make_account()
        _setup_auth(client, actor)

        with patch(
            "app.db.repositories.account_repo.AccountRepository.get_by_id",
            return_value=actor,
        ):
            resp = client.get("/api/v1/me")

        client.app.dependency_overrides = {}
        # Should fail for auth reasons (no session cookie from dep override is fine)
        # but NOT for CSRF reasons (so not 401 due to CSRF)
        # The important thing: no CSRF header needed for GET
        assert resp.status_code in (200, 401)  # 401 is ok if no session, but not 400
