"""TASK-025: API dependency tests."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import _SESSION_COOKIE, get_session, get_session_service
from app.api.errors import register_error_handlers
from app.auth.session import Session as UserSession
from app.auth.session import SessionService
from app.db.models.account import Account, AccountStatus, UserType


def _make_session(account_id: uuid.UUID | None = None) -> UserSession:
    from datetime import UTC, datetime, timedelta
    now = datetime.now(UTC)
    return UserSession(
        session_id="test-session-id",
        account_id=account_id or uuid.uuid4(),
        role=UserType.PATIENT,
        created_at=now,
        last_seen_at=now,
        ip="1.2.3.4",
        absolute_expires_at=now + timedelta(hours=8),
    )


def _app_with_session_route(mock_svc: SessionService) -> FastAPI:
    from fastapi import Depends
    app = FastAPI()
    register_error_handlers(app)

    def override_svc() -> SessionService:
        return mock_svc

    app.dependency_overrides[get_session_service] = override_svc

    @app.get("/me")
    async def me(session: UserSession = Depends(get_session)) -> dict[str, str]:
        return {"account_id": str(session.account_id)}

    return app


def test_get_session_returns_session_when_cookie_valid() -> None:
    acct_id = uuid.uuid4()
    session = _make_session(acct_id)
    mock_svc = MagicMock(spec=SessionService)
    mock_svc.resolve.return_value = session

    app = _app_with_session_route(mock_svc)
    client = TestClient(app, raise_server_exceptions=False)
    client.cookies.set(_SESSION_COOKIE, "test-session-id")
    resp = client.get("/me")
    assert resp.status_code == 200
    assert resp.json()["account_id"] == str(acct_id)


def test_get_session_raises_401_when_no_cookie() -> None:
    mock_svc = MagicMock(spec=SessionService)
    app = _app_with_session_route(mock_svc)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/me")
    assert resp.status_code == 401
    assert resp.headers["content-type"].startswith("application/problem+json")


def test_get_session_raises_401_when_session_expired() -> None:
    mock_svc = MagicMock(spec=SessionService)
    mock_svc.resolve.return_value = None  # expired

    app = _app_with_session_route(mock_svc)
    client = TestClient(app, raise_server_exceptions=False)
    client.cookies.set(_SESSION_COOKIE, "expired-session-id")
    resp = client.get("/me")
    assert resp.status_code == 401


def test_get_current_user_raises_401_for_deactivated_account() -> None:
    from fastapi import Depends

    from app.api.deps import get_current_user

    acct_id = uuid.uuid4()
    session = _make_session(acct_id)
    mock_svc = MagicMock(spec=SessionService)
    mock_svc.resolve.return_value = session

    mock_account = MagicMock(spec=Account)
    mock_account.status = AccountStatus.DEACTIVATED

    app = FastAPI()
    register_error_handlers(app)
    app.dependency_overrides[get_session_service] = lambda: mock_svc

    from app.db.repositories.account_repo import AccountRepository
    from app.db.repositories.session import get_db

    def override_db():
        yield MagicMock()

    app.dependency_overrides[get_db] = override_db

    @app.get("/profile")
    async def profile(account: Account = Depends(get_current_user)) -> dict[str, str]:
        return {"id": str(account.id)}

    with patch.object(AccountRepository, "__init__", return_value=None):
        with patch.object(AccountRepository, "get_by_id", return_value=mock_account):
            client = TestClient(app, raise_server_exceptions=False)
            client.cookies.set(_SESSION_COOKIE, "test-session-id")
            resp = client.get("/profile")

    assert resp.status_code == 401


def test_get_current_user_raises_401_for_inactive_account() -> None:
    from fastapi import Depends
    from unittest.mock import patch

    from app.api.deps import get_current_user
    from app.db.repositories.account_repo import AccountRepository
    from app.db.repositories.session import get_db

    acct_id = uuid.uuid4()
    session = _make_session(acct_id)
    mock_svc = MagicMock(spec=SessionService)
    mock_svc.resolve.return_value = session

    mock_account = MagicMock(spec=Account)
    mock_account.status = AccountStatus.INACTIVE

    app = FastAPI()
    register_error_handlers(app)
    app.dependency_overrides[get_session_service] = lambda: mock_svc

    def override_db():
        yield MagicMock()

    app.dependency_overrides[get_db] = override_db

    @app.get("/profile2")
    async def profile2(account: Account = Depends(get_current_user)) -> dict[str, str]:
        return {"id": str(account.id)}

    with patch.object(AccountRepository, "__init__", return_value=None):
        with patch.object(AccountRepository, "get_by_id", return_value=mock_account):
            client = TestClient(app, raise_server_exceptions=False)
            client.cookies.set(_SESSION_COOKIE, "test-session-id")
            resp = client.get("/profile2")

    assert resp.status_code == 401
