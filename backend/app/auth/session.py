"""SessionService — Redis-backed opaque session tokens (TASK-021).

Token: secrets.token_urlsafe(32) — no user data embedded.
Redis keys:
  session:{session_id}              → JSON; TTL = inactivity timeout
  account_sessions:{account_id}     → sorted set; score = created_at timestamp
"""

from __future__ import annotations

import json
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import redis

from app.core.config import get_settings
from app.db.models.account import Account, UserType

# Inactivity timeouts by role group
_CLINICAL_ROLES = {UserType.DOCTOR, UserType.PATIENT}
_ADMIN_ROLES = {UserType.ADMIN, UserType.SYSADMIN}

_SETTINGS_DEFAULTS = {
    "SESSION_INACTIVITY_CLINICAL_SECONDS": 900,
    "SESSION_INACTIVITY_ADMIN_SECONDS": 1800,
    "SESSION_ABSOLUTE_LIFETIME_SECONDS": 28800,
    "SESSION_MAX_CONCURRENT": 3,
}


def _session_key(session_id: str) -> str:
    return f"session:{session_id}"


def _account_sessions_key(account_id: str) -> str:
    return f"account_sessions:{account_id}"


@dataclass
class Session:
    session_id: str
    account_id: uuid.UUID
    role: UserType
    created_at: datetime
    last_seen_at: datetime
    ip: str | None
    absolute_expires_at: datetime


@dataclass
class CreateSessionResult:
    session: Session
    evicted_session_id: str | None  # set if an old session was evicted


class SessionService:
    """Redis-backed session management."""

    def __init__(self, redis_client: redis.Redis) -> None:
        self._redis = redis_client
        s = get_settings()
        self._inactivity_clinical: int = s.session_inactivity_clinical_seconds
        self._inactivity_admin: int = s.session_inactivity_admin_seconds
        self._absolute_lifetime: int = s.session_absolute_lifetime_seconds
        self._max_concurrent: int = s.session_max_concurrent

    def _inactivity_ttl(self, role: UserType) -> int:
        if role in _CLINICAL_ROLES:
            return self._inactivity_clinical
        return self._inactivity_admin

    def create_session(self, account: Account, ip: str | None = None) -> CreateSessionResult:
        """Create a new session. Evicts oldest if concurrency cap is exceeded."""
        now = datetime.now(UTC)
        session_id = secrets.token_urlsafe(32)
        absolute_expires_at = datetime.fromtimestamp(now.timestamp() + self._absolute_lifetime, UTC)

        session = Session(
            session_id=session_id,
            account_id=account.id,
            role=account.user_type,
            created_at=now,
            last_seen_at=now,
            ip=ip,
            absolute_expires_at=absolute_expires_at,
        )

        ttl = self._inactivity_ttl(account.user_type)
        payload = _session_to_dict(session)
        account_key = _account_sessions_key(str(account.id))

        # Evict oldest session if at cap
        evicted_session_id: str | None = None
        existing: list[bytes | str] = self._redis.zrange(account_key, 0, -1)  # type: ignore[assignment]
        if len(existing) >= self._max_concurrent:
            raw_oldest = existing[0]
            oldest_id: str = (
                raw_oldest.decode() if isinstance(raw_oldest, bytes) else str(raw_oldest)
            )
            self._redis.delete(_session_key(oldest_id))
            self._redis.zrem(account_key, oldest_id)
            evicted_session_id = oldest_id

        # Store session
        self._redis.setex(_session_key(session_id), ttl, json.dumps(payload))
        # Add to account's sorted set (score = created_at timestamp)
        self._redis.zadd(account_key, {session_id: now.timestamp()})
        # TTL the sorted set to absolute lifetime to prevent orphans
        self._redis.expire(account_key, self._absolute_lifetime)

        return CreateSessionResult(session=session, evicted_session_id=evicted_session_id)

    def resolve(self, session_id: str) -> Session | None:
        """Look up a session by ID, refresh its sliding TTL, return None if expired/missing."""
        raw = self._redis.get(_session_key(session_id))
        if raw is None:
            return None

        data = json.loads(raw)
        session = _session_from_dict(data)

        now = datetime.now(UTC)
        # Enforce absolute expiry
        if now >= session.absolute_expires_at:
            self.invalidate(session_id)
            return None

        # Slide TTL (capped by absolute_expires_at)
        ttl = self._inactivity_ttl(session.role)
        remaining_absolute = int((session.absolute_expires_at - now).total_seconds())
        effective_ttl = min(ttl, remaining_absolute)

        # Update last_seen_at
        session = Session(
            session_id=session.session_id,
            account_id=session.account_id,
            role=session.role,
            created_at=session.created_at,
            last_seen_at=now,
            ip=session.ip,
            absolute_expires_at=session.absolute_expires_at,
        )
        self._redis.setex(
            _session_key(session_id), effective_ttl, json.dumps(_session_to_dict(session))
        )
        return session

    def invalidate(self, session_id: str) -> None:
        """Delete a single session. Idempotent."""
        raw = self._redis.get(_session_key(session_id))
        if raw is not None:
            data = json.loads(raw)
            account_id = data.get("account_id")
            if account_id:
                self._redis.zrem(_account_sessions_key(account_id), session_id)
        self._redis.delete(_session_key(session_id))

    def list_account_session_ids(self, account_id: uuid.UUID) -> list[str]:
        """Return all active session IDs for an account."""
        account_key = _account_sessions_key(str(account_id))
        raw_ids: list[bytes | str] = self._redis.zrange(account_key, 0, -1)  # type: ignore[assignment]
        return [sid.decode() if isinstance(sid, bytes) else str(sid) for sid in raw_ids]

    def get_inactivity_expiry(self, session: Session) -> datetime:
        """Compute the inactivity expiry deadline for a resolved session."""
        now = datetime.now(UTC)
        ttl = self._inactivity_ttl(session.role)
        remaining_absolute = int((session.absolute_expires_at - now).total_seconds())
        effective_ttl = min(ttl, max(0, remaining_absolute))
        return datetime.fromtimestamp(now.timestamp() + effective_ttl, UTC)

    def invalidate_all(self, account_id: uuid.UUID) -> None:
        """Delete all sessions for an account. Idempotent."""
        account_key = _account_sessions_key(str(account_id))
        session_ids: list[bytes | str] = self._redis.zrange(account_key, 0, -1)  # type: ignore[assignment]
        for sid in session_ids:
            sid_str: str = sid.decode() if isinstance(sid, bytes) else str(sid)
            self._redis.delete(_session_key(sid_str))
        self._redis.delete(account_key)


def _session_to_dict(session: Session) -> dict[str, object]:
    return {
        "session_id": session.session_id,
        "account_id": str(session.account_id),
        "role": session.role.value,
        "created_at": session.created_at.isoformat(),
        "last_seen_at": session.last_seen_at.isoformat(),
        "ip": session.ip,
        "absolute_expires_at": session.absolute_expires_at.isoformat(),
    }


def _session_from_dict(data: dict[str, object]) -> Session:
    return Session(
        session_id=str(data["session_id"]),
        account_id=uuid.UUID(str(data["account_id"])),
        role=UserType(data["role"]),
        created_at=datetime.fromisoformat(str(data["created_at"])),
        last_seen_at=datetime.fromisoformat(str(data["last_seen_at"])),
        ip=data.get("ip"),  # type: ignore[arg-type]
        absolute_expires_at=datetime.fromisoformat(str(data["absolute_expires_at"])),
    )
