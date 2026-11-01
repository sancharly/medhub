"""The secret-setting rule (SR-041 AC 3, SR-022 AC 3, ADD-026 U-DEP-SecretRule).

One list of secret settings and one list of known placeholders, used by the API start-up, the
Celery worker and beat start-up, and the ``object-store-preflight`` Compose service. A secret
that is unset, empty or a known placeholder is refused, and an ``AT_REST_ENCRYPTION_KEY`` that
does not decode to 32 bytes is refused. The messages name the setting and never carry a value.

This module imports nothing from ``app.core.config`` at import time, so the preflight can use it
without a complete application environment.
"""

from __future__ import annotations

import base64
import os
from collections.abc import Mapping
from urllib.parse import unquote, urlsplit

# Every secret setting, by environment-variable name. ``check`` is driven by this list and so is
# the audit flow scan (backend/tests/audit/test_audit_no_secrets.py), so the two cannot drift.
DATABASE_URL = "DATABASE_URL"
DATABASE_OWNER_URL = "DATABASE_OWNER_URL"  # only in the db-migrate service (TASK-191)
SMTP_PASSWORD = "SMTP_PASSWORD"  # only checked when SMTP_USER is set (CR-004 Q-5)
AT_REST_ENCRYPTION_KEY = "AT_REST_ENCRYPTION_KEY"
AT_REST_ENCRYPTION_RETIRED_KEYS = "AT_REST_ENCRYPTION_RETIRED_KEYS"  # comma-separated, optional
OBJECT_STORE_SSE_KEY = "OBJECT_STORE_SSE_KEY"  # optional
OBJECT_STORE_ACCESS_KEY = "OBJECT_STORE_ACCESS_KEY"
OBJECT_STORE_SECRET_KEY = "OBJECT_STORE_SECRET_KEY"

SECRET_SETTINGS = (
    DATABASE_URL,
    DATABASE_OWNER_URL,
    SMTP_PASSWORD,
    AT_REST_ENCRYPTION_KEY,
    AT_REST_ENCRYPTION_RETIRED_KEYS,
    OBJECT_STORE_SSE_KEY,
    OBJECT_STORE_ACCESS_KEY,
    OBJECT_STORE_SECRET_KEY,
)
_REQUIRED = (DATABASE_URL, AT_REST_ENCRYPTION_KEY, OBJECT_STORE_ACCESS_KEY, OBJECT_STORE_SECRET_KEY)

# Weak words, compared in lower case. The object-store credential rule has always refused these.
KNOWN_DEFAULTS = frozenset({"minioadmin", "changeme", "admin", "password", "secret"})
# Every secret value infra/.env.example has shipped, plus the weak words. Do not remove an entry:
# an operator who copied an old template still has the value.
KNOWN_PLACEHOLDERS = KNOWN_DEFAULTS | {
    "change-me",
    "change-me-to-a-random-32-byte-secret",
    "change-me-to-a-random-32-byte-key!",
}
PLACEHOLDER_PREFIX = "change-me"  # any value starting with this is a placeholder

MIN_OBJECT_STORE_SECRET_LENGTH = 16
AT_REST_KEY_BYTES = 32


def is_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return lowered in KNOWN_PLACEHOLDERS or lowered.startswith(PLACEHOLDER_PREFIX)


def check_value(name: str, value: str | None, min_length: int = 0) -> list[str]:
    """Return one rejection per problem, each naming ``name``; empty when the value passes."""
    if value is None:
        return [f"{name} is not set"]
    value = value.strip()
    if value == "":
        return [f"{name} is empty"]
    problems = []
    if is_placeholder(value):
        problems.append(f"{name} is a known default value")
    if len(value) < min_length:
        problems.append(f"{name} is shorter than {min_length} characters")
    return problems


def _key_problem(name: str, value: str) -> list[str]:
    """The key must be base64 of exactly 32 bytes (same decoding as app.db.crypto)."""
    try:
        length = len(base64.urlsafe_b64decode(value.strip().encode()))
    except Exception:  # noqa: BLE001 — never include the value or the decoder's message
        return [f"{name} is not valid base64"]
    if length != AT_REST_KEY_BYTES:
        return [f"{name} must decode to {AT_REST_KEY_BYTES} bytes, got {length}"]
    return []


def _database_password(url: str) -> str | None:
    try:
        password = urlsplit(url).password
    except ValueError:
        return None
    return unquote(password) if password is not None else None


def _one(name: str, value: str | None) -> list[str]:
    if name in (DATABASE_URL, DATABASE_OWNER_URL):
        if value is None or value.strip() == "":
            return [f"{name} is not set"]
        password = _database_password(value)
        if password is None:
            return [f"{name} has no password or is not a valid URL"]
        return check_value(f"{name} (password)", password)
    if name == OBJECT_STORE_SECRET_KEY:
        return check_value(name, value, MIN_OBJECT_STORE_SECRET_LENGTH)
    problems = check_value(name, value)
    if not problems and name == AT_REST_ENCRYPTION_KEY and value is not None:
        problems = _key_problem(name, value)
    return problems


def _database_user(url: str) -> str | None:
    try:
        return urlsplit(url).username
    except ValueError:
        return None


def _roles_problems(env: Mapping[str, str | None]) -> list[str]:
    """The runtime role and the owner role must differ in name and in password (ADR-0017)."""
    runtime = (env.get(DATABASE_URL) or "").strip()
    owner = (env.get(DATABASE_OWNER_URL) or "").strip()
    if not runtime or not owner:
        return []
    problems = []
    if _database_user(runtime) == _database_user(owner):
        problems.append(f"{DATABASE_URL} and {DATABASE_OWNER_URL} name the same database user")
    runtime_password = _database_password(runtime)
    if runtime_password is not None and runtime_password == _database_password(owner):
        problems.append(f"{DATABASE_URL} and {DATABASE_OWNER_URL} have the same password")
    return problems


def secret_values(env: Mapping[str, str | None]) -> list[str]:
    """The secret values ``env`` configures, for scans that must never find them in output.

    Empty values are skipped. The database password is returned, not the whole URL.
    """
    values: list[str] = []
    for name in SECRET_SETTINGS:
        raw = env.get(name)
        if not raw or not raw.strip():
            continue
        if name in (DATABASE_URL, DATABASE_OWNER_URL):
            password = _database_password(raw)
            values.extend([password] if password else [])
        elif name == AT_REST_ENCRYPTION_RETIRED_KEYS:
            values.extend(k.strip() for k in raw.split(",") if k.strip())
        else:
            values.append(raw.strip())
    return values


def check(env: Mapping[str, str | None]) -> list[str]:
    """Return one message per problem in the secret settings of ``env``; empty when all pass."""
    problems: list[str] = []
    for name in _REQUIRED:
        problems += _one(name, env.get(name))
    # SMTP without authentication is supported; the password is required only with a user.
    if (env.get("SMTP_USER") or "").strip():
        problems += _one(SMTP_PASSWORD, env.get(SMTP_PASSWORD))
    # Optional settings are checked only when present.
    for name in (DATABASE_OWNER_URL, OBJECT_STORE_SSE_KEY):
        if (env.get(name) or "").strip():
            problems += _one(name, env.get(name))
    problems += _roles_problems(env)
    for key in (env.get(AT_REST_ENCRYPTION_RETIRED_KEYS) or "").split(","):
        if key.strip():
            problems += check_value(AT_REST_ENCRYPTION_RETIRED_KEYS, key) or _key_problem(
                AT_REST_ENCRYPTION_RETIRED_KEYS, key
            )
    return problems


def settings_env() -> dict[str, str | None]:
    """The configured secrets by environment-variable name (Settings fields plus optional ones)."""
    from app.core.config import get_settings  # noqa: PLC0415

    s = get_settings()
    env: dict[str, str | None] = {
        DATABASE_URL: str(s.database_url),
        "SMTP_USER": s.smtp_user,
        SMTP_PASSWORD: s.smtp_password.get_secret_value() if s.smtp_password else None,
        AT_REST_ENCRYPTION_KEY: s.at_rest_encryption_key.get_secret_value(),
        OBJECT_STORE_ACCESS_KEY: s.object_store_access_key.get_secret_value(),
        OBJECT_STORE_SECRET_KEY: s.object_store_secret_key.get_secret_value(),
    }
    for name in (DATABASE_OWNER_URL, AT_REST_ENCRYPTION_RETIRED_KEYS, OBJECT_STORE_SSE_KEY):
        env[name] = os.environ.get(name)
    return env


def enforce(env: Mapping[str, str | None] | None = None) -> None:
    """Refuse to start (``SystemExit``) when a secret setting fails ``check``.

    Without ``env`` the configured Settings are checked. The message names settings only.
    """
    problems = check(settings_env() if env is None else env)
    if problems:
        raise SystemExit(
            "refusing to start, secret settings rejected:\n"
            + "\n".join("  - " + p for p in problems)
        )
