"""Object-store credential rule (SR-040 AC 2, SR-041 AC 5, CR-002 Q-2, ADD-025 U-OBJ-Preflight).

One rule (the shared placeholder list is in ``app.core.secret_settings``), used by the
``object-store-preflight`` Compose service before the object store and
its bucket initialiser start. It is independent of the server product. It checks the two S3
credentials and the store's SSE key: ``OBJECT_STORE_SSE_KEY`` must be set, base64 of 32 bytes and
different from ``AT_REST_ENCRYPTION_KEY`` and every retired field key, which it receives for that
comparison (ADR-0018). The functions never return or print a key value.
"""

import os
import sys

from app.core.secret_settings import (
    AT_REST_ENCRYPTION_KEY,
    AT_REST_ENCRYPTION_RETIRED_KEYS,
    MIN_OBJECT_STORE_SECRET_LENGTH,
    OBJECT_STORE_ACCESS_KEY,
    OBJECT_STORE_SECRET_KEY,
    OBJECT_STORE_SSE_KEY,
    check_value,
    sse_key_problems,
)
from app.core.secret_settings import KNOWN_DEFAULTS as KNOWN_DEFAULTS  # noqa: PLC0414

ACCESS_KEY_VAR = OBJECT_STORE_ACCESS_KEY
SECRET_KEY_VAR = OBJECT_STORE_SECRET_KEY
MIN_SECRET_LENGTH = MIN_OBJECT_STORE_SECRET_LENGTH


def check(access_key: str | None, secret_key: str | None) -> list[str]:
    """Return one rejection per problem, each naming the setting; empty when both keys pass."""
    return check_value(ACCESS_KEY_VAR, access_key) + check_value(
        SECRET_KEY_VAR, secret_key, MIN_SECRET_LENGTH
    )


def check_sse_key(
    sse_key: str | None, field_key: str | None, retired_keys: str | None
) -> list[str]:
    """Rejections of the SSE key; the field key must be given so the two can be compared."""
    problems = sse_key_problems(sse_key, field_key, retired_keys)
    if not (field_key or "").strip():
        problems.append(f"{AT_REST_ENCRYPTION_KEY} is not set, so the two keys cannot be compared")
    return problems


def main() -> int:
    env = os.environ
    rejections = check(env.get(ACCESS_KEY_VAR), env.get(SECRET_KEY_VAR)) + check_sse_key(
        env.get(OBJECT_STORE_SSE_KEY),
        env.get(AT_REST_ENCRYPTION_KEY),
        env.get(AT_REST_ENCRYPTION_RETIRED_KEYS),
    )
    for rejection in rejections:
        print(f"object-store credential rejected: {rejection}", file=sys.stderr)
    return 1 if rejections else 0


if __name__ == "__main__":
    sys.exit(main())
