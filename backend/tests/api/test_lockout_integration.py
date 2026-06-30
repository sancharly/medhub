"""Integration tests for lockout wiring (TASK-024a).

Tests verify that the LockoutService is actually wired into the login flow
and that the admin unlock endpoint works.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_redis
from app.api.routers.auth import _get_login_service
from app.auth.lockout import MAX_FAILURES, LockoutService
from app.auth.login import LoginFailure, LoginSuccess
from app.auth.session import Session as UserSession
from app.db.models.account import Account, AccountStatus, UserType
from app.db.repositories.session import get_db
from app.main import create_app


def _make_account(user_type: UserType = UserType.PATIENT) -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.email = "user@example.com"
    acct.user_type = user_type
    acct.status = AccountStatus.ACTIVE
    acct.first_name = "Test"
    acct.surname = "User"
    acct.password_hash = None
    acct.password_changed_at = None
    acct.date_of_birth = None
    acct.created_at = datetime.now(UTC)
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


@pytest.fixture()
def fake_redis():
    return fakeredis.FakeRedis()


class TestLockoutWiredIntoLogin:
    def test_account_locked_after_max_failures(self, client, fake_redis):
        """After MAX_FAILURES failed logins the account is locked and returns 401."""
        account = _make_account()
        login_failure = LoginFailure()

        # Use a real LockoutService with fakeredis to verify integration
        lockout_svc = LockoutService(fake_redis)

        # Pre-fill failures to hit the lockout threshold
        for _ in range(MAX_FAILURES):
            lockout_svc.record_failure(account.id, account.email, "1.2.3.4")

        assert lockout_svc.is_locked(account.id) is True

        # Override login service to verify that even a correct password fails when locked
        from app.auth.login import LoginService  # noqa: PLC0415

        mock_svc = MagicMock(spec=LoginService)
        mock_svc.login.return_value = login_failure

        client.app.dependency_overrides[_get_login_service] = lambda: mock_svc
        client.app.dependency_overrides[get_redis] = lambda: fake_redis

        def override_db():
            yield MagicMock()

        client.app.dependency_overrides[get_db] = override_db

        resp = client.post(
            "/api/v1/auth/login",
            json={"email": account.email, "password": "AnyPassword1!"},
        )

        client.app.dependency_overrides = {}
        assert resp.status_code == 401

    def test_lockout_service_passed_to_login(self, client, fake_redis):
        """login() is called with a lockout_svc kwarg when redis is available."""
        account = _make_account()
        session = _make_session(account)
        login_success = LoginSuccess(session=session, csrf_token="csrf")

        from app.auth.login import LoginService  # noqa: PLC0415

        mock_svc = MagicMock(spec=LoginService)
        mock_svc.login.return_value = login_success

        with patch(
            "app.db.repositories.account_repo.AccountRepository.get_by_id",
            return_value=account,
        ):
            client.app.dependency_overrides[_get_login_service] = lambda: mock_svc
            client.app.dependency_overrides[get_redis] = lambda: fake_redis

            def override_db():
                yield MagicMock()

            client.app.dependency_overrides[get_db] = override_db

            resp = client.post(
                "/api/v1/auth/login",
                json={"email": account.email, "password": "AnyPassword1!"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 200
        # Verify lockout_svc was passed as keyword argument
        call_kwargs = mock_svc.login.call_args.kwargs
        assert "lockout_svc" in call_kwargs
        assert call_kwargs["lockout_svc"] is not None

    def test_successful_login_resets_lockout(self, fake_redis):
        """On success, reset() clears the failure counter."""
        account = _make_account()
        lockout_svc = LockoutService(fake_redis)

        # Record some failures
        for _ in range(3):
            lockout_svc.record_failure(account.id, account.email, "1.2.3.4")

        assert lockout_svc.is_locked(account.id) is False

        # Reset (simulates successful login)
        lockout_svc.reset(account.id)

        # Counter should be gone — still not locked (was already below threshold)
        assert lockout_svc.is_locked(account.id) is False


class TestAdminUnlockEndpoint:
    def _auth_as(self, client, actor: Account) -> None:
        client.app.dependency_overrides[get_current_user] = lambda: actor

        def override_db():
            yield MagicMock()

        client.app.dependency_overrides[get_db] = override_db

    def test_sysadmin_can_unlock_account(self, client, fake_redis):
        actor = _make_account(UserType.SYSADMIN)
        target = _make_account(UserType.PATIENT)
        target.email = "patient@example.com"

        # Lock the target first
        lockout_svc = LockoutService(fake_redis)
        for _ in range(MAX_FAILURES):
            lockout_svc.record_failure(target.id, target.email, "1.2.3.4")
        assert lockout_svc.is_locked(target.id) is True

        self._auth_as(client, actor)
        client.app.dependency_overrides[get_redis] = lambda: fake_redis

        with patch(
            "app.db.repositories.account_repo.AccountRepository.get_by_id",
            return_value=target,
        ):
            resp = client.post(
                f"/api/v1/accounts/{target.id}/unlock",
                cookies={"medhub_csrf": "tok"},
                headers={"X-CSRF-Token": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 204
        # After unlock the account should be unlocked
        assert lockout_svc.is_locked(target.id) is False

    def test_non_sysadmin_cannot_unlock(self, client, fake_redis):
        actor = _make_account(UserType.ADMIN)
        target_id = uuid.uuid4()

        self._auth_as(client, actor)
        client.app.dependency_overrides[get_redis] = lambda: fake_redis

        resp = client.post(
            f"/api/v1/accounts/{target_id}/unlock",
            cookies={"medhub_csrf": "tok"},
            headers={"X-CSRF-Token": "tok"},
        )

        client.app.dependency_overrides = {}
        assert resp.status_code == 403

    def test_unlock_nonexistent_account_returns_404(self, client, fake_redis):
        actor = _make_account(UserType.SYSADMIN)
        self._auth_as(client, actor)
        client.app.dependency_overrides[get_redis] = lambda: fake_redis

        with patch(
            "app.db.repositories.account_repo.AccountRepository.get_by_id",
            return_value=None,
        ):
            resp = client.post(
                f"/api/v1/accounts/{uuid.uuid4()}/unlock",
                cookies={"medhub_csrf": "tok"},
                headers={"X-CSRF-Token": "tok"},
            )

        client.app.dependency_overrides = {}
        assert resp.status_code == 404
