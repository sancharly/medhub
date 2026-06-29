"""Security headers middleware (TASK-069)."""

from __future__ import annotations

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

# Paths exempt from CSRF because no session exists at these points.
_CSRF_EXEMPT_PREFIXES = (
    "/api/v1/auth/login",
    "/api/v1/auth/password-reset",
    "/api/v1/activation",
    "/api/v1/anonymized-data/",  # ADR-0013: no-session retrieval
    "/api/v1/healthz",
    "/api/v1/openapi.json",
    "/healthz",
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
        if request.method in _UNSAFE_METHODS and not any(
            request.url.path.startswith(prefix) for prefix in _CSRF_EXEMPT_PREFIXES
        ):
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
