"""The one module-key pattern (SR-023 AC 9, ADD-013).

Used by module discovery to accept a manifest and by the audit writer to accept a module key as
a ``target_id``, so the two cannot drift apart. Shape only: no registry lookup.
"""

import re

MODULE_KEY = re.compile(r"[a-z][a-z0-9_-]{0,63}")


def is_valid_module_key(value: object) -> bool:
    return isinstance(value, str) and MODULE_KEY.fullmatch(value) is not None
