"""Security headers middleware (TASK-069)."""

from __future__ import annotations

import re
import secrets
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none';"
)

_SECURITY_HEADERS = {
    "Content-Security-Policy": _CSP,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    # HSTS: 1-year max-age; the reverse proxy also sets this for HTTP→HTTPS redirect
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers[header] = value
        return response


_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Paths exempt from CSRF because no session exists at these points (SR-031 AC 3, PRB-003).
# Exemptions are exact: a sibling or child path is enforced unless it is listed here.
_CSRF_EXEMPT_PATHS = frozenset(
    {
        "/api/v1/auth/login",  # POST login: the session does not exist yet
        "/api/v1/anonymized-data/retrieve",  # ADR-0013: no-session retrieval
        "/api/v1/healthz",  # health probe, no session
        "/api/v1/openapi.json",  # contract document, no session
        "/healthz",  # container health probe, no session
    }
)
# Routes with a path parameter: one whole-path pattern per route, one segment per parameter.
_CSRF_EXEMPT_PATTERNS = (
    # POST /api/v1/activation/{token}: the invited user has no session yet
    re.compile(r"/api/v1/activation/[^/]+"),
)


def is_csrf_exempt(path: str) -> bool:
    """True when ``path`` is a deliberately no-session route (one trailing slash ignored)."""
    path = path.removesuffix("/")
    return path in _CSRF_EXEMPT_PATHS or any(
        pattern.fullmatch(path) for pattern in _CSRF_EXEMPT_PATTERNS
    )


_CSRF_COOKIE = "medhub_csrf"
_CSRF_HEADER = "X-CSRF-Token"

_CSRF_403 = {
    "type": "https://medhub.example/errors/forbidden",
    "title": "Forbidden",
    "status": 403,
    "detail": "CSRF token missing or invalid.",
    "errors": [],
}


class CsrfEnforcementMiddleware(BaseHTTPMiddleware):
    """Enforce CSRF for all state-changing requests except exempt public paths."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method in _UNSAFE_METHODS and not is_csrf_exempt(request.url.path):
            cookie_token = request.cookies.get(_CSRF_COOKIE)
            header_token = request.headers.get(_CSRF_HEADER)
            if (
                not cookie_token
                or not header_token
                or not secrets.compare_digest(cookie_token, header_token)
            ):
                return JSONResponse(
                    content={**_CSRF_403, "instance": request.url.path},
                    status_code=403,
                    media_type="application/problem+json",
                )
        return await call_next(request)
