"""Hardened session cookie helpers (TASK-022)."""

from __future__ import annotations

from fastapi import Response

from app.core.config import get_settings

_SESSION_COOKIE = "medhub_session"
_MAX_AGE = 28800  # 8h — matches SESSION_ABSOLUTE_LIFETIME_SECONDS


def set_session_cookie(response: Response, session_id: str) -> None:
    """Write the HttpOnly, Secure, SameSite=strict session cookie."""
    secure = get_settings().session_cookie_secure
    response.set_cookie(
        key=_SESSION_COOKIE,
        value=session_id,
        httponly=True,
        secure=secure,
        samesite="strict",
        path="/",
        max_age=_MAX_AGE,
    )


def clear_session_cookie(response: Response) -> None:
    """Expire the session cookie."""
    response.delete_cookie(
        key=_SESSION_COOKIE,
        path="/",
        samesite="strict",
    )
