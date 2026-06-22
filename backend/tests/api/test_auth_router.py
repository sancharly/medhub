"""Tests for auth endpoints (TASK-060)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_redis, get_session, get_session_service
from app.api.routers.auth import _get_login_service
from app.auth.login import LoginFailure, LoginService, LoginSuccess
from app.auth.session import Session as UserSession
from app.auth.session import SessionService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.repositories.session import get_db
from app.main import create_app


def _make_account(
    user_type: UserType = UserType.DOCTOR,
    status: AccountStatus = AccountStatus.ACTIVE,
) -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.email = "test@example.com"
    acct.user_type = user_type
    acct.status = status
    acct.first_name = "Jane"
    acct.surname = "Doe"
    acct.password_hash = None
    acct.password_changed_at = None
    acct.date_of_birth = None
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


def _auth_as(client, actor: Account) -> UserSession:
    session = _make_session(actor)
    mock_svc = MagicMock(spec=SessionService)
    mock_svc.resolve.return_value = session
    client.app.dependency_overrides[get_session_service] = lambda: mock_svc
    client.app.dependency_overrides[get_current_user] = lambda: actor
    client.app.dependency_overrides[get_session] = lambda: session

    def override_db():
        yield MagicMock()

    client.app.dependency_overrides[get_db] = override_db
    return session


class TestLoginEndpoint:
    def test_login_success_returns_user(self, client):
        account = _make_account()
        session = _make_session(account)
        login_success = LoginSuccess(session=session, csrf_token="test-csrf")

        mock_login_svc = MagicMock(spec=LoginService)
        mock_login_svc.login.return_value = login_success

        with patch(
            "app.db.repositories.account_repo.AccountRepository.get_by_id",
            return_value=account,
        ):
            client.app.dependency_overrides[_get_login_service] = lambda: mock_login_svc
            client.app.dependency_overrides[get_redis] = lambda: MagicMock()

            def override_db():
                yield MagicMock()

            client.app.dependency_overrides[get_db] = override_db

            resp = client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "Password123!"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        data = resp.json()
        assert "user" in data
        assert data["user"]["accountType"] == account.user_type.value
        assert "mustChangePassword" in data
        assert "evictedSession" in data

    def test_login_failure_returns_401(self, client):
        login_failure = LoginFailure()
        mock_login_svc = MagicMock(spec=LoginService)
        mock_login_svc.login.return_value = login_failure

        client.app.dependency_overrides[_get_login_service] = lambda: mock_login_svc
        client.app.dependency_overrides[get_redis] = lambda: MagicMock()

        def override_db():
            yield MagicMock()

        client.app.dependency_overrides[get_db] = override_db

        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "bad@example.com", "password": "wrongpassword"},
        )

        client.app.dependency_overrides = {}
        assert resp.status_code == 401
        assert resp.headers["content-type"].startswith("application/problem+json")

    def test_login_missing_fields_returns_error(self, client):
        resp = client.post("/api/v1/auth/login", json={})
        assert resp.status_code in (400, 422)

    def test_login_missing_password_returns_error(self, client):
        resp = client.post("/api/v1/auth/login", json={"email": "test@example.com"})
        assert resp.status_code in (400, 422)


class TestLogoutEndpoint:
    def test_logout_invalidates_session(self, client):
        account = _make_account()
        _auth_as(client, account)
        mock_svc = client.app.dependency_overrides[get_session_service]()

        resp = client.post(
            "/api/v1/auth/logout",
            cookies={"medhub_session": "test-session-id", "medhub_csrf": "token123"},
            headers={"X-CSRF-Token": "token123"},
        )

        client.app.dependency_overrides = {}
        assert resp.status_code == 204
        mock_svc.invalidate.assert_called_once_with("test-session-id")

    def test_logout_requires_auth(self, client):
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 401

    def test_logout_requires_csrf(self, client):
        account = _make_account()
        _auth_as(client, account)

        resp = client.post(
            "/api/v1/auth/logout",
            cookies={"medhub_session": "test-session-id"},
        )

        client.app.dependency_overrides = {}
        assert resp.status_code == 401


class TestSessionExtendEndpoint:
    def test_extend_returns_expiry(self, client):
        account = _make_account()
        _auth_as(client, account)

        resp = client.post(
            "/api/v1/auth/session/extend",
            cookies={"medhub_session": "test-session-id", "medhub_csrf": "token123"},
            headers={"X-CSRF-Token": "token123"},
        )

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        data = resp.json()
        assert "expiresAt" in data

    def test_extend_requires_auth(self, client):
        resp = client.post("/api/v1/auth/session/extend")
        assert resp.status_code == 401
