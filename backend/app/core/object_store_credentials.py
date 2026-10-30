"""Object-store credential rule (SR-040 AC 2, CR-002 Q-2, ADD-025 U-OBJ-Preflight).

One rule, used by the ``object-store-preflight`` Compose service before the object store and
its bucket initialiser start. It is independent of the server product. The functions never
return or print a key value.
"""

import os
import sys

ACCESS_KEY_VAR = "OBJECT_STORE_ACCESS_KEY"
SECRET_KEY_VAR = "OBJECT_STORE_SECRET_KEY"

KNOWN_DEFAULTS = frozenset({"minioadmin", "changeme", "admin", "password", "secret"})
MIN_SECRET_LENGTH = 16


def _check_one(name: str, value: str | None, min_length: int = 0) -> list[str]:
    if value is None:
        return [f"{name} is not set"]
    value = value.strip()
    if value == "":
        return [f"{name} is empty"]
    problems = []
    if value.lower() in KNOWN_DEFAULTS:
        problems.append(f"{name} is a known default value")
    if len(value) < min_length:
        problems.append(f"{name} is shorter than {min_length} characters")
    return problems


def check(access_key: str | None, secret_key: str | None) -> list[str]:
    """Return one rejection per problem, each naming the setting; empty when both keys pass."""
    return _check_one(ACCESS_KEY_VAR, access_key) + _check_one(
        SECRET_KEY_VAR, secret_key, MIN_SECRET_LENGTH
    )


def main() -> int:
    rejections = check(os.environ.get(ACCESS_KEY_VAR), os.environ.get(SECRET_KEY_VAR))
    for rejection in rejections:
        print(f"object-store credential rejected: {rejection}", file=sys.stderr)
    return 1 if rejections else 0


if __name__ == "__main__":
    sys.exit(main())
