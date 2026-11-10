"""Tests for CSRF enforcement middleware (TASK-069a).

Covers:
- Middleware rejects state-changing requests without valid CSRF token → 403
- Middleware passes valid CSRF tokens through to the route layer
- Safe methods (GET) are never blocked
- Public no-session paths (login, activation) are exempt
- TASK-139 / PRB-003: exemptions are exact (sibling and child paths are enforced) and a
  route inventory pins every exempt route to a reviewed list (SR-031 AC 3)
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_session_service
from app.auth.session import Session as UserSession
from app.auth.session import SessionService
from app.core import security_middleware
from app.core.security_middleware import is_csrf_exempt
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

    @pytest.mark.parametrize(
        ("content_type", "body"),
        [
            ("application/x-www-form-urlencoded", "email=a%40b.com&password=wrong"),
            ("text/plain", '{"email": "a@b.com", "password": "wrong"}'),
            ("multipart/form-data; boundary=x", "--x--"),
        ],
    )
    def test_login_refuses_a_non_json_post_without_calling_the_service(
        self, client, content_type, body
    ):
        """Login CSRF defence (SR-031): a cross-site <form> can only send these three
        content types, and the login route accepts JSON only, so the service is never reached."""
        with patch("app.auth.login.LoginService.login") as login:
            resp = client.post(
                "/api/v1/auth/login", content=body, headers={"Content-Type": content_type}
            )
        assert resp.status_code == 400
        login.assert_not_called()

    def test_login_has_no_cors_so_a_cross_origin_json_post_cannot_pass_a_preflight(self, client):
        resp = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert resp.status_code == 405
        assert "access-control-allow-origin" not in resp.headers

    def test_activation_post_exempt_from_csrf(self, client):
        resp = client.post(
            "/api/v1/activation/invalid-token",
            json={"password": "Test1234!"},
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


# --- TASK-139 / PRB-003 / SR-031 AC 3 --------------------------------------------------------

_UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}

# Reviewed list: the only unsafe routes allowed to be CSRF-exempt (no session exists at them).
# Adding a route here is a security decision; a reviewer must agree why it has no session.
_REVIEWED_EXEMPT_ROUTES = {
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/activation/{token}"),
    ("POST", "/api/v1/anonymized-data/retrieve"),  # ADR-0013
}
_REVIEWED_EXEMPT_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/anonymized-data/retrieve",
    "/api/v1/healthz",
    "/api/v1/openapi.json",
    "/healthz",
}
_REVIEWED_EXEMPT_PATTERNS = {r"/api/v1/activation/[^/]+"}


def _unsafe_routes(routes, prefix=""):
    """Yield (method, path template) for every state-changing route, through nested includes."""
    for route in routes:
        if hasattr(route, "original_router"):  # FastAPI lazily included router
            yield from _unsafe_routes(
                route.original_router.routes, prefix + route.include_context.prefix
            )
        elif getattr(route, "methods", None):
            for method in route.methods & _UNSAFE:
                yield method, prefix + route.path
        elif hasattr(route, "routes"):
            yield from _unsafe_routes(route.routes, prefix + getattr(route, "path", ""))


def _concrete(template: str) -> str:
    return re.sub(r"\{[^}]+\}", "x", template)


class TestCsrfExemptionIsExact:
    """SR-031 AC 3 (TASK-139, PRB-003): prefix siblings are enforced, exact routes stay exempt."""

    @pytest.mark.parametrize(
        ("method", "path"),
        [
            ("POST", "/api/v1/activation-x"),
            ("POST", "/api/v1/activation"),
            ("POST", "/api/v1/activation/abc/extra"),
            ("POST", "/api/v1/auth/password-reset"),
            ("POST", "/api/v1/auth/password-reset-force"),
            ("POST", "/api/v1/auth/login-x"),
            ("POST", "/api/v1/auth/login/extra"),
            ("POST", "/api/v1/anonymized-data/retrieve-all"),
            ("POST", "/api/v1/anonymized-data/other"),
            ("POST", "/api/v1/healthz-x"),
            ("POST", "/api/v1/openapi.json.bak"),
            ("POST", "/healthz/deep"),
            ("PUT", "/api/v1/activation-x"),
            ("DELETE", "/api/v1/activation/abc/extra"),
        ],
    )
    def test_sibling_path_without_token_is_403_problem_json(self, client, method, path):
        """AC 3: sibling and child paths of an exempt route are CSRF-enforced."""
        resp = client.request(method, path)
        assert resp.status_code == 403
        assert resp.headers["content-type"] == "application/problem+json"
        assert "CSRF" in resp.json()["detail"]

    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/auth/login",
            "/api/v1/auth/login/",
            "/api/v1/activation/abc",
            "/api/v1/anonymized-data/retrieve",
            "/api/v1/healthz",
            "/api/v1/openapi.json",
            "/healthz",
        ],
    )
    def test_exact_exempt_paths_work_without_session_or_token(self, client, path):
        """AC 2: the legitimately exempt routes are reachable sessionless (not 403 CSRF)."""
        resp = client.post(path, json={})
        assert not (resp.status_code == 403 and "CSRF token missing" in resp.text)

    def test_is_csrf_exempt_table(self):
        """AC 1/2: matcher truth table (method-independent; exemption is by exact path)."""
        exempt = [
            "/api/v1/auth/login",
            "/api/v1/auth/login/",
            "/api/v1/activation/abc",
            "/api/v1/anonymized-data/retrieve",
            "/api/v1/healthz",
            "/api/v1/openapi.json",
            "/healthz",
        ]
        enforced = [
            "/api/v1/auth/login-x",
            "/api/v1/auth/login//",
            "/api/v1/auth/login/extra",
            "/api/v1/auth/password-reset",
            "/api/v1/auth/logout",
            "/api/v1/activation",
            "/api/v1/activation/",
            "/api/v1/activation-x",
            "/api/v1/activation/abc/extra",
            "/api/v1/anonymized-data",
            "/api/v1/anonymized-data/retrieve-all",
            "/api/v1/healthz-x",
            "/healthz/deep",
            "/api/v1/accounts/x/resend-activation",
            "/api/v1/modules/x/y",  # module routers are enforced (TASK-139)
        ]
        assert all(is_csrf_exempt(p) for p in exempt)
        assert not any(is_csrf_exempt(p) for p in enforced)

    def test_new_sibling_route_is_enforced_not_silently_exempt(self, app):
        """AC 3: a route added later next to an exempt one is enforced without a decision."""

        @app.post("/api/v1/activation-admin")
        def _new_route() -> dict[str, bool]:
            return {"ok": True}

        resp = TestClient(app, raise_server_exceptions=False).post("/api/v1/activation-admin")
        assert resp.status_code == 403


class TestCsrfRouteInventory:
    """AC 3 (negative control): exemptions are pinned to a reviewed list."""

    def test_inventory_finds_the_application_routes(self, app):
        routes = set(_unsafe_routes(app.routes))
        assert ("POST", "/api/v1/auth/login") in routes
        assert ("POST", "/api/v1/appointments") in routes
        assert len(routes) >= 20  # guards against the walker silently seeing nothing

    def test_exempt_routes_equal_the_reviewed_list(self, app):
        exempt = {(m, t) for m, t in _unsafe_routes(app.routes) if is_csrf_exempt(_concrete(t))}
        assert exempt == _REVIEWED_EXEMPT_ROUTES

    def test_every_other_unsafe_route_is_403_without_a_token(self, client):
        for method, template in sorted(_unsafe_routes(client.app.routes)):
            if (method, template) in _REVIEWED_EXEMPT_ROUTES:
                continue
            resp = client.request(method, _concrete(template))
            assert resp.status_code == 403, (method, template)

    def test_exemption_constants_equal_the_reviewed_list(self):
        """A new exact path or pattern fails here until it is added to the reviewed list."""
        assert set(security_middleware._CSRF_EXEMPT_PATHS) == _REVIEWED_EXEMPT_PATHS
        assert {p.pattern for p in security_middleware._CSRF_EXEMPT_PATTERNS} == (
            _REVIEWED_EXEMPT_PATTERNS
        )
