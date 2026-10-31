"""Object-store credential rule (SR-040 AC 2, CR-002 Q-2, ADD-025 U-OBJ-Preflight).

One rule (the shared placeholder list is in ``app.core.secret_settings``), used by the
``object-store-preflight`` Compose service before the object store and
its bucket initialiser start. It is independent of the server product. The functions never
return or print a key value.
"""

import os
import sys

from app.core.secret_settings import KNOWN_DEFAULTS as KNOWN_DEFAULTS  # noqa: PLC0414
from app.core.secret_settings import (
    MIN_OBJECT_STORE_SECRET_LENGTH,
    OBJECT_STORE_ACCESS_KEY,
    OBJECT_STORE_SECRET_KEY,
    check_value,
)

ACCESS_KEY_VAR = OBJECT_STORE_ACCESS_KEY
SECRET_KEY_VAR = OBJECT_STORE_SECRET_KEY
MIN_SECRET_LENGTH = MIN_OBJECT_STORE_SECRET_LENGTH


def check(access_key: str | None, secret_key: str | None) -> list[str]:
    """Return one rejection per problem, each naming the setting; empty when both keys pass."""
    return check_value(ACCESS_KEY_VAR, access_key) + check_value(
        SECRET_KEY_VAR, secret_key, MIN_SECRET_LENGTH
    )


def main() -> int:
    rejections = check(os.environ.get(ACCESS_KEY_VAR), os.environ.get(SECRET_KEY_VAR))
    for rejection in rejections:
        print(f"object-store credential rejected: {rejection}", file=sys.stderr)
    return 1 if rejections else 0


if __name__ == "__main__":
    sys.exit(main())
