"""CSRF token issuance and validation (TASK-022).

Strategy: double-submit cookie.
  - medhub_csrf cookie: HttpOnly=False, Secure, SameSite=strict
  - Client must send X-CSRF-Token header matching the cookie on state-changing methods
  - Comparison via secrets.compare_digest (constant-time)
"""

from __future__ import annotations

import secrets

from fastapi import Request, Response

from app.api.errors import UnauthenticatedError
from app.core.config import get_settings

_CSRF_COOKIE = "medhub_csrf"
_CSRF_HEADER = "X-CSRF-Token"
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class CsrfError(UnauthenticatedError):
    def __init__(self, detail: str = "CSRF token missing or invalid.") -> None:
        super().__init__(detail)


def issue_csrf_token(response: Response) -> str:
    """Set the CSRF cookie (not HttpOnly) and return the raw token."""
    token = secrets.token_urlsafe(32)
    secure = get_settings().session_cookie_secure
    response.set_cookie(
        key=_CSRF_COOKIE,
        value=token,
        httponly=False,  # must be readable by JS
        secure=secure,
        samesite="strict",
        path="/",
    )
    return token


async def require_csrf(request: Request) -> None:
    """FastAPI dependency — validate CSRF for state-changing methods."""
    if request.method in _SAFE_METHODS:
        return

    cookie_token = request.cookies.get(_CSRF_COOKIE)
    header_token = request.headers.get(_CSRF_HEADER)

    if not cookie_token or not header_token:
        raise CsrfError()

    # Constant-time comparison prevents timing attacks
    if not secrets.compare_digest(cookie_token, header_token):
        raise CsrfError()
