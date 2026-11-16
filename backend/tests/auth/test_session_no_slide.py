"""TASK-221 (HIGH 1): ``GET /me/modules`` checks the session without extending it.

The client polls the module list every 50 s (SR-015 AC 5). A poll that slid the session would keep
it alive for as long as a view stays open, so the server inactivity timeout (SR-030 AC 1, AC 2;
RISK-005) would never run. Every other authenticated route still slides.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.api.deps import _SESSION_COOKIE, get_session_service
from app.auth.session import SessionService, _session_key
from app.db.models.account import Account, AccountStatus, UserType
from app.db.repositories.session import get_db
from app.main import create_app


def _account(user_type: UserType = UserType.PATIENT) -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.email = "user@example.com"
    acct.user_type = user_type
    acct.status = AccountStatus.ACTIVE
    acct.first_name = "Jane"
    acct.surname = "Doe"
    acct.date_of_birth = None
    acct.created_at = datetime.now(UTC)
    acct.password_changed_at = None
    return acct


# --- service level ---


def test_resolve_without_slide_leaves_ttl_and_last_seen_alone() -> None:
    r = fakeredis.FakeRedis()
    svc = SessionService(r)
    s = svc.create_session(_account()).session
    r.expire(_session_key(s.session_id), 100)
    stored = r.get(_session_key(s.session_id))

    resolved = svc.resolve(s.session_id, slide=False)

    assert resolved is not None
    assert resolved.account_id == s.account_id
    assert r.ttl(_session_key(s.session_id)) <= 100
    assert r.get(_session_key(s.session_id)) == stored


def test_resolve_without_slide_returns_none_for_missing() -> None:
    assert SessionService(fakeredis.FakeRedis()).resolve("nope", slide=False) is None


def test_resolve_without_slide_enforces_absolute_expiry() -> None:
    r = fakeredis.FakeRedis()
    svc = SessionService(r)
    s = svc.create_session(_account()).session
    future = s.absolute_expires_at + timedelta(seconds=1)
    with patch("app.auth.session.datetime") as mock_dt:
        mock_dt.now.return_value = future
        mock_dt.fromtimestamp.side_effect = datetime.fromtimestamp
        mock_dt.fromisoformat.side_effect = datetime.fromisoformat
        assert svc.resolve(s.session_id, slide=False) is None
    assert not r.exists(_session_key(s.session_id))


# --- route level ---


@pytest.fixture()
def env():
    r = fakeredis.FakeRedis()
    svc = SessionService(r)
    actor = _account()
    app = create_app()
    app.dependency_overrides[get_session_service] = lambda: svc
    app.dependency_overrides[get_db] = lambda: iter([MagicMock()])
    client = TestClient(app, raise_server_exceptions=False)
    repo = MagicMock()
    repo.get_by_id.return_value = actor
    modules_repo = MagicMock()
    modules_repo.enabled_module_keys_for_groups.return_value = ["dicom-viewer"]
    groups_repo = MagicMock()
    groups_repo.memberships_for_account.return_value = []
    with (
        patch("app.api.deps.AccountRepository", return_value=repo),
        patch("app.api.routers.me.GroupRepository", return_value=groups_repo),
        patch("app.api.routers.me.ModuleRepository", return_value=modules_repo),
    ):
        yield client, r, svc, svc.create_session(actor).session


def _get(client: TestClient, path: str, session_id: str):
    client.cookies.set(_SESSION_COOKIE, session_id)
    return client.get(path)


def test_polling_my_modules_does_not_extend_the_session(env) -> None:
    client, r, svc, s = env
    r.expire(_session_key(s.session_id), 100)
    before = svc.remaining_seconds(svc.resolve(s.session_id, slide=False))  # type: ignore[arg-type]
    last_seen = r.get(_session_key(s.session_id))

    for _ in range(3):
        resp = _get(client, "/api/v1/me/modules", s.session_id)
        assert resp.status_code == 200
        assert resp.json() == {"modules": ["dicom-viewer"]}

    assert r.ttl(_session_key(s.session_id)) <= 100
    assert r.get(_session_key(s.session_id)) == last_seen  # last_seen_at not rewritten
    after = svc.remaining_seconds(svc.resolve(s.session_id, slide=False))  # type: ignore[arg-type]
    assert after <= before


def test_my_modules_with_an_expired_session_is_401(env) -> None:
    client, r, _svc, s = env
    r.delete(_session_key(s.session_id))

    assert _get(client, "/api/v1/me/modules", s.session_id).status_code == 401


def test_my_modules_with_a_session_past_its_absolute_lifetime_is_401(env) -> None:
    client, r, _svc, s = env
    future = s.absolute_expires_at + timedelta(seconds=1)
    with patch("app.auth.session.datetime") as mock_dt:
        mock_dt.now.return_value = future
        mock_dt.fromtimestamp.side_effect = datetime.fromtimestamp
        mock_dt.fromisoformat.side_effect = datetime.fromisoformat
        resp = _get(client, "/api/v1/me/modules", s.session_id)

    assert resp.status_code == 401
    assert not r.exists(_session_key(s.session_id))


def test_my_modules_with_an_ended_session_is_401(env) -> None:
    """A logout, eviction or password-change kill (``invalidate``) is honoured, not undone."""
    client, r, svc, s = env
    svc.invalidate(s.session_id)

    assert _get(client, "/api/v1/me/modules", s.session_id).status_code == 401
    assert not r.exists(_session_key(s.session_id))


def test_my_modules_for_an_inactive_account_is_401(env) -> None:
    client, _r, _svc, s = env
    repo = MagicMock()
    repo.get_by_id.return_value = _account()
    repo.get_by_id.return_value.status = AccountStatus.DEACTIVATED
    with patch("app.api.deps.AccountRepository", return_value=repo):
        assert _get(client, "/api/v1/me/modules", s.session_id).status_code == 401


def test_my_modules_without_a_cookie_is_401(env) -> None:
    client, *_ = env
    client.cookies.clear()

    assert client.get("/api/v1/me/modules").status_code == 401


def test_other_routes_still_slide_the_session(env) -> None:
    client, r, _svc, s = env
    r.expire(_session_key(s.session_id), 100)
    stored = r.get(_session_key(s.session_id))

    resp = _get(client, "/api/v1/me", s.session_id)

    assert resp.status_code == 200
    assert r.ttl(_session_key(s.session_id)) > 100
    assert r.get(_session_key(s.session_id)) != stored
