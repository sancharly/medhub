"""Build a ``Content-Disposition`` header value for any file name (TASK-204, PRB-063).

The only place in the application that builds this header (SR-013 AC 3). The value is
pure ASCII (RFC 6266 section 4.3): an ASCII fallback ``filename`` and an RFC 5987
``filename*`` carrying the exact name as percent-encoded UTF-8. Never raises for any ``str``.
"""

from __future__ import annotations

import unicodedata
from urllib.parse import quote

_FALLBACK_NAME = "download"


def _neutralise_controls(name: str) -> str:
    """Map control characters (Cc) and lone surrogates (Cs) to ``_``."""
    return "".join("_" if unicodedata.category(c) in ("Cc", "Cs") else c for c in name)


def _ascii_fallback(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", name)
    chars = []
    for c in decomposed:
        if unicodedata.category(c) == "Mn":
            continue
        chars.append(c if " " <= c <= "~" and c not in '"\\' else "_")
    fallback = "".join(chars)
    if not fallback.strip(". "):
        return _FALLBACK_NAME
    return fallback


def content_disposition(filename: str, disposition: str = "attachment") -> str:
    """Return ``<disposition>; filename="<ascii>"; filename*=UTF-8''<encoded>``."""
    name = _neutralise_controls(filename)
    encoded = quote(name, safe="")
    return f"{disposition}; filename=\"{_ascii_fallback(name)}\"; filename*=UTF-8''{encoded}"
