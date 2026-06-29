"""Tests for CSRF enforcement middleware (TASK-069a).

Covers:
- Middleware rejects state-changing requests without valid CSRF token → 403
- Middleware passes valid CSRF tokens through to the route layer
- Safe methods (GET) are never blocked
- Public no-session paths (login, activation) are exempt
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_session_service
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


def _auth_as(client, actor: Account) -> None:
    """Override auth deps so route logic runs without a real DB."""
    client.app.dependency_overrides[get_current_user] = lambda: actor

    def override_db():
        yield MagicMock()

    client.app.dependency_overrides[get_db] = override_db


def _auth_via_session(client, actor: Account) -> None:
    """Override session-based auth deps (used by logout)."""
    session = _make_session(actor)
    mock_svc = MagicMock(spec=SessionService)
    mock_svc.resolve.return_value = session
    client.app.dependency_overrides[get_session_service] = lambda: mock_svc

    def override_db():
        yield MagicMock()

    client.app.dependency_overrides[get_db] = override_db


class TestCsrfMiddlewareMissingToken:
    """Requests without CSRF token on state-changing routes → 403."""

    def test_post_appointments_without_csrf_returns_403(self, client):
        _auth_as(client, _make_account())
        resp = client.post("/api/v1/appointments", json={})
        client.app.dependency_overrides = {}
        assert resp.status_code == 403
        assert resp.headers["content-type"] == "application/problem+json"

    def test_post_accounts_without_csrf_returns_403(self, client):
        _auth_as(client, _make_account(UserType.ADMIN))
        resp = client.post("/api/v1/accounts", json={})
        client.app.dependency_overrides = {}
        assert resp.status_code == 403

    def test_post_groups_without_csrf_returns_403(self, client):
        _auth_as(client, _make_account())
        resp = client.post("/api/v1/groups", json={})
        client.app.dependency_overrides = {}
        assert resp.status_code == 403

    def test_post_clinical_attachment_without_csrf_returns_403(self, client):
        _auth_as(client, _make_account())
        entry_id = uuid.uuid4()
        resp = client.post(f"/api/v1/clinical-entries/{entry_id}/attachments", content=b"data")
        client.app.dependency_overrides = {}
        assert resp.status_code == 403

    def test_put_group_module_without_csrf_returns_403(self, client):
        _auth_as(client, _make_account())
        group_id = uuid.uuid4()
        resp = client.put(f"/api/v1/groups/{group_id}/modules/some-module")
        client.app.dependency_overrides = {}
        assert resp.status_code == 403

    def test_delete_group_member_without_csrf_returns_403(self, client):
        _auth_as(client, _make_account())
        group_id = uuid.uuid4()
        member_id = uuid.uuid4()
        resp = client.delete(f"/api/v1/groups/{group_id}/members/{member_id}")
        client.app.dependency_overrides = {}
        assert resp.status_code == 403


class TestCsrfMiddlewareMismatch:
    """Cookie token ≠ header token → 403."""

    def test_csrf_mismatch_returns_403(self, client):
        _auth_as(client, _make_account())
        resp = client.post(
            "/api/v1/appointments",
            json={},
            cookies={"medhub_csrf": "cookie-token"},
            headers={"X-CSRF-Token": "different-token"},
        )
        client.app.dependency_overrides = {}
        assert resp.status_code == 403


class TestCsrfMiddlewareValidToken:
    """Valid CSRF token passes the middleware (route layer may return other errors)."""

    def test_post_appointments_with_valid_csrf_passes_middleware(self, client):
        _auth_as(client, _make_account())
        resp = client.post(
            "/api/v1/appointments",
            json={},
            cookies={"medhub_csrf": "valid-token"},
            headers={"X-CSRF-Token": "valid-token"},
        )
        client.app.dependency_overrides = {}
        # 403 would mean CSRF block; any other code means the request reached the route
        assert resp.status_code != 403

    def test_post_groups_with_valid_csrf_passes_middleware(self, client):
        _auth_as(client, _make_account())
        resp = client.post(
            "/api/v1/groups",
            json={},
            cookies={"medhub_csrf": "valid-token"},
            headers={"X-CSRF-Token": "valid-token"},
        )
        client.app.dependency_overrides = {}
        assert resp.status_code != 403


class TestCsrfSafeMethods:
    """GET/HEAD/OPTIONS are never blocked regardless of CSRF state."""

    def test_get_does_not_require_csrf(self, client):
        _auth_as(client, _make_account())
        resp = client.get("/api/v1/appointments")
        client.app.dependency_overrides = {}
        # Any status except 403 (CSRF block) is acceptable
        assert resp.status_code != 403

    def test_get_me_does_not_require_csrf(self, client):
        _auth_as(client, _make_account())
        resp = client.get("/api/v1/me")
        client.app.dependency_overrides = {}
        assert resp.status_code != 403


class TestCsrfExemptPaths:
    """Public no-session paths must be exempt from CSRF."""

    def test_login_post_exempt_from_csrf(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "a@b.com", "password": "wrong"},
        )
        # 401/422 from auth logic is fine; 403 would mean CSRF blocked a public path
        assert resp.status_code != 403

    def test_activation_post_exempt_from_csrf(self, client):
        resp = client.post(
            "/api/v1/activation",
            json={"token": "invalid", "password": "Test1234!"},
        )
        assert resp.status_code != 403

    def test_logout_without_csrf_now_returns_403(self, client):
        """Logout is NOT in the exempt list — middleware enforces CSRF before the
        per-route require_csrf dep runs."""
        actor = _make_account()
        _auth_via_session(client, actor)

        with patch(
            "app.db.repositories.account_repo.AccountRepository.get_by_id",
            return_value=actor,
        ):
            resp = client.post(
                "/api/v1/auth/logout",
                cookies={"medhub_session": "test-session-id"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 403

    def test_logout_with_valid_csrf_succeeds(self, client):
        actor = _make_account()
        _auth_via_session(client, actor)

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


class TestCsrfProblemJsonShape:
    """403 CSRF errors must be application/problem+json."""

    def test_403_response_is_problem_json(self, client):
        resp = client.post("/api/v1/appointments", json={})
        assert resp.status_code == 403
        assert resp.headers["content-type"] == "application/problem+json"
        body = resp.json()
        assert body["status"] == 403
        assert "CSRF" in body["detail"]
        assert body["title"] == "Forbidden"
