"""TASK-022: Cookie and CSRF tests."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.auth.cookies import clear_session_cookie, set_session_cookie
from app.auth.csrf import _CSRF_COOKIE, _CSRF_HEADER, issue_csrf_token, require_csrf

# --- session cookie helpers ---

def test_set_session_cookie_sets_httponly() -> None:
    from fastapi import FastAPI
    from fastapi.responses import Response
    from starlette.testclient import TestClient

    app = FastAPI()

    @app.get("/set")
    def set_cookie_route() -> Response:
        resp = Response(content="ok")
        set_session_cookie(resp, "test-session-id")
        return resp

    client = TestClient(app)
    resp = client.get("/set")
    cookie_header = resp.headers.get("set-cookie", "")
    assert "medhub_session" in cookie_header
    assert "httponly" in cookie_header.lower()
    assert "samesite=strict" in cookie_header.lower()


def test_clear_session_cookie_expires_it() -> None:
    from fastapi import FastAPI
    from fastapi.responses import Response
    from starlette.testclient import TestClient

    app = FastAPI()

    @app.get("/clear")
    def clear_route() -> Response:
        resp = Response(content="ok")
        clear_session_cookie(resp)
        return resp

    client = TestClient(app)
    resp = client.get("/clear")
    assert "medhub_session" in resp.headers.get("set-cookie", "")


# --- CSRF ---

def _csrf_app() -> FastAPI:
    """Minimal app for CSRF tests."""

    app = FastAPI()

    @app.get("/issue-csrf")
    def issue() -> dict[str, str]:
        # Return token in body for testing
        resp = JSONResponse({"ok": True})
        token = issue_csrf_token(resp)
        resp.body = f'{{"token": "{token}"}}'.encode()
        return resp  # type: ignore[return-value]

    @app.post("/protected", dependencies=[])
    async def protected(request: Request) -> dict[str, str]:
        await require_csrf(request)
        return {"ok": "true"}

    return app


def test_csrf_safe_method_bypasses_check() -> None:
    from fastapi import Depends, FastAPI

    app = FastAPI()

    @app.get("/safe", dependencies=[Depends(require_csrf)])
    async def safe() -> dict[str, str]:
        return {"ok": "true"}

    client = TestClient(app)
    resp = client.get("/safe")  # GET is safe — no CSRF needed
    assert resp.status_code == 200


def test_csrf_post_without_token_raises() -> None:
    from fastapi import Depends, FastAPI

    from app.api.errors import register_error_handlers

    app = FastAPI()
    register_error_handlers(app)

    @app.post("/protected", dependencies=[Depends(require_csrf)])
    async def protected() -> dict[str, str]:
        return {"ok": "true"}

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/protected", json={})
    assert resp.status_code == 401


def test_csrf_post_with_mismatched_token_raises() -> None:
    from fastapi import Depends, FastAPI

    from app.api.errors import register_error_handlers

    app = FastAPI()
    register_error_handlers(app)

    @app.post("/protected", dependencies=[Depends(require_csrf)])
    async def protected() -> dict[str, str]:
        return {"ok": "true"}

    client = TestClient(app, raise_server_exceptions=False)
    # Cookie and header differ
    client.cookies.set(_CSRF_COOKIE, "token-a")
    resp = client.post("/protected", json={}, headers={_CSRF_HEADER: "token-b"})
    assert resp.status_code == 401


def test_csrf_post_with_matching_token_succeeds() -> None:
    from fastapi import Depends, FastAPI

    from app.api.errors import register_error_handlers

    app = FastAPI()
    register_error_handlers(app)

    @app.post("/protected", dependencies=[Depends(require_csrf)])
    async def protected() -> dict[str, str]:
        return {"ok": "true"}

    client = TestClient(app, raise_server_exceptions=False)
    token = "matching-csrf-token-123"
    client.cookies.set(_CSRF_COOKIE, token)
    resp = client.post("/protected", json={}, headers={_CSRF_HEADER: token})
    assert resp.status_code == 200


def test_issue_csrf_token_sets_non_httponly_cookie() -> None:
    from fastapi import FastAPI
    from fastapi.responses import Response
    from starlette.testclient import TestClient

    app = FastAPI()

    @app.get("/csrf-issue")
    def csrf_issue_route() -> Response:
        resp = Response(content="ok")
        issue_csrf_token(resp)
        return resp

    client = TestClient(app)
    resp = client.get("/csrf-issue")
    cookie_header = resp.headers.get("set-cookie", "")
    assert _CSRF_COOKIE in cookie_header
    # Should NOT be HttpOnly — JS needs to read it
    assert "httponly" not in cookie_header.lower()
