"""The secret-setting rule (SR-041 AC 3, SR-022 AC 3, ADD-026 U-DEP-SecretRule).

One list of secret settings and one list of known placeholders, used by the API start-up, the
Celery worker and beat start-up, and the ``object-store-preflight`` Compose service. A secret
that is unset, empty or a known placeholder is refused, and an ``AT_REST_ENCRYPTION_KEY`` that
does not decode to 32 bytes is refused. The key identifier and the retired ``id:key`` entries are
checked too (SR-022 AC 3, AC 6, ADR-0018). The messages name the setting and never carry a value.

This module imports nothing from ``app.core.config`` at import time, so the preflight can use it
without a complete application environment.
"""

from __future__ import annotations

import base64
import os
import re
from collections.abc import Mapping
from urllib.parse import unquote, urlsplit

# Every secret setting, by environment-variable name. ``check`` is driven by this list and so is
# the audit flow scan (backend/tests/audit/test_audit_no_secrets.py), so the two cannot drift.
DATABASE_URL = "DATABASE_URL"
DATABASE_OWNER_URL = "DATABASE_OWNER_URL"  # only in the db-migrate service (TASK-191)
SMTP_PASSWORD = "SMTP_PASSWORD"  # only checked when SMTP_USER is set (CR-004 Q-5)
AT_REST_ENCRYPTION_KEY = "AT_REST_ENCRYPTION_KEY"
# Not a secret: the identifier of the current key, written into every new field ciphertext
# (SR-022 AC 6, ADR-0018). Required; checked by ``check`` but not in SECRET_SETTINGS.
AT_REST_ENCRYPTION_KEY_ID = "AT_REST_ENCRYPTION_KEY_ID"
# Optional, comma-separated ``id:base64key`` entries; used for decryption only (ADR-0018).
AT_REST_ENCRYPTION_RETIRED_KEYS = "AT_REST_ENCRYPTION_RETIRED_KEYS"
# The object store's server-side-encryption key (SR-041 AC 5, ADR-0018). Required by the Compose
# stack and by the ``object-store-preflight`` service; the Python services do not receive it, so
# ``check`` verifies it only when it is present.
OBJECT_STORE_SSE_KEY = "OBJECT_STORE_SSE_KEY"
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
KEY_ID_PATTERN = re.compile(r"[a-z0-9-]{1,32}")


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


def _decoded(value: str | None) -> bytes | None:
    """The decoded key bytes, or None when it does not decode (reported elsewhere)."""
    if not value:
        return None
    try:
        return base64.urlsafe_b64decode(value.strip().encode())
    except Exception:  # noqa: BLE001
        return None


def key_id_problems(name: str, key_id: str | None) -> list[str]:
    """A key identifier is 1 to 32 characters of ``[a-z0-9-]``, checked exactly as it is used.

    No stripping: the value is written into every ciphertext as it is, so a space or newline
    around it would make every value written under it unreadable. A blank value is "not set".
    """
    if key_id is None or key_id.strip() == "":
        return [f"{name} is not set"]
    if not KEY_ID_PATTERN.fullmatch(key_id):
        return [f"{name} must be 1 to 32 characters of a-z, 0-9 and '-', with no whitespace"]
    return []


def split_retired_keys(raw: str | None) -> list[tuple[str, str]]:
    """The ``id:key`` entries of the retired-keys setting, split at the first ``:``.

    Blank entries are skipped. The id is kept exactly as written (``keyring_problems`` refuses
    whitespace in it); the key part is stripped by its readers. An entry with no ``:`` yields an
    empty id, which ``keyring_problems`` reports by position.
    """
    entries = [e for e in (raw or "").split(",") if e.strip()]
    return [tuple(e.split(":", 1)) if ":" in e else ("", e) for e in entries]  # type: ignore[misc]


def keyring_problems(key_id: str | None, key: str | None, retired_raw: str | None) -> list[str]:
    """Problems in the key id and the retired keys, each naming the setting (never a key value).

    Refuses a bad or missing id, an entry that is not ``id:key``, a duplicate id (also against the
    current id), a key that is a placeholder or does not decode to 32 bytes, and a retired key
    equal to the current key.
    """
    problems = key_id_problems(AT_REST_ENCRYPTION_KEY_ID, key_id)
    name = AT_REST_ENCRYPTION_RETIRED_KEYS
    seen = {key_id} if key_id and not problems else set()
    current = _decoded(key)
    for position, (kid, value) in enumerate(split_retired_keys(retired_raw), start=1):
        entry_name = f"{name} entry {position}"
        if kid == "":
            problems.append(f"{entry_name} is not in the form id:key")
            continue
        if not KEY_ID_PATTERN.fullmatch(kid):
            problems.append(
                f"{entry_name} has an invalid key id (1 to 32 characters of a-z, 0-9, '-')"
            )
        elif kid in seen:
            problems.append(f"{entry_name} repeats the key id '{kid}'")
        seen.add(kid)
        found = check_value(entry_name, value) or _key_problem(entry_name, value)
        problems += found
        if not found and current is not None and _decoded(value) == current:
            problems.append(f"{entry_name} is the same key as AT_REST_ENCRYPTION_KEY")
    return problems


def sse_key_problems(
    sse_key: str | None, field_key: str | None, retired_raw: str | None
) -> list[str]:
    """Problems in the object-store SSE key, each naming a setting (never a key value).

    Refuses an unset, empty or placeholder key, one that is not base64 of 32 bytes, and one that
    equals ``AT_REST_ENCRYPTION_KEY`` or a retired field key (compared as decoded bytes), because
    a key shared with field encryption cannot be rotated on its own (ADR-0018).
    """
    problems = _one(OBJECT_STORE_SSE_KEY, sse_key)
    sse = _decoded(sse_key)
    if problems or sse is None:
        return problems
    if sse == _decoded(field_key):
        problems.append(f"{OBJECT_STORE_SSE_KEY} is the same key as {AT_REST_ENCRYPTION_KEY}")
    for position, (_, value) in enumerate(split_retired_keys(retired_raw), start=1):
        if sse == _decoded(value):
            problems.append(
                f"{OBJECT_STORE_SSE_KEY} is the same key as "
                f"{AT_REST_ENCRYPTION_RETIRED_KEYS} entry {position}"
            )
    return problems


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
    if (
        not problems
        and name in (AT_REST_ENCRYPTION_KEY, OBJECT_STORE_SSE_KEY)
        and value is not None
    ):
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
            values.extend(key.strip() for _, key in split_retired_keys(raw))
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
    if (env.get(DATABASE_OWNER_URL) or "").strip():
        problems += _one(DATABASE_OWNER_URL, env.get(DATABASE_OWNER_URL))
    if (env.get(OBJECT_STORE_SSE_KEY) or "").strip():
        problems += sse_key_problems(
            env.get(OBJECT_STORE_SSE_KEY),
            env.get(AT_REST_ENCRYPTION_KEY),
            env.get(AT_REST_ENCRYPTION_RETIRED_KEYS),
        )
    problems += _roles_problems(env)
    problems += keyring_problems(
        env.get(AT_REST_ENCRYPTION_KEY_ID),
        env.get(AT_REST_ENCRYPTION_KEY),
        env.get(AT_REST_ENCRYPTION_RETIRED_KEYS),
    )
    return problems


def settings_env() -> dict[str, str | None]:
    """The configured secrets by environment-variable name (the owner URL: from the process)."""
    from app.core.config import get_settings  # noqa: PLC0415

    s = get_settings()
    env: dict[str, str | None] = {
        DATABASE_URL: str(s.database_url),
        "SMTP_USER": s.smtp_user,
        SMTP_PASSWORD: s.smtp_password.get_secret_value() if s.smtp_password else None,
        AT_REST_ENCRYPTION_KEY: s.at_rest_encryption_key.get_secret_value(),
        AT_REST_ENCRYPTION_KEY_ID: s.at_rest_encryption_key_id,
        AT_REST_ENCRYPTION_RETIRED_KEYS: (
            s.at_rest_encryption_retired_keys.get_secret_value()
            if s.at_rest_encryption_retired_keys
            else None
        ),
        OBJECT_STORE_ACCESS_KEY: s.object_store_access_key.get_secret_value(),
        OBJECT_STORE_SECRET_KEY: s.object_store_secret_key.get_secret_value(),
        OBJECT_STORE_SSE_KEY: (
            s.object_store_sse_key.get_secret_value() if s.object_store_sse_key else None
        ),
        DATABASE_OWNER_URL: os.environ.get(DATABASE_OWNER_URL),
    }
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
