"""Build a ``Content-Disposition`` header value for any file name (TASK-204, PRB-063).

The only place in the application that builds this header (SR-013 AC 3). The value is
pure ASCII (RFC 6266 section 4.3): an ASCII fallback ``filename`` and an RFC 5987
``filename*`` carrying the exact name as percent-encoded UTF-8. Never raises for any ``str``.

The value is bounded whatever name is stored (SR-013 AC 3, PRB-069): ``filename*`` carries at most
255 UTF-8 bytes of the name and the fallback at most 150 characters, each keeping the extension, so
the header stays near 1 KB and always fits the proxy's 4 KB header buffer.
"""

from __future__ import annotations

import unicodedata
from urllib.parse import quote

_FALLBACK_NAME = "download"
_MAX_NAME_BYTES = 255
_MAX_FALLBACK_CHARS = 150
_MAX_EXTENSION_CHARS = 16
# Unicode bidirectional controls (Cf): they can reorder the displayed name (TASK-204 QA finding 3).
# Other Cf characters stay, e.g. U+200D (zero-width joiner) is part of emoji sequences.
_BIDI_CONTROLS = frozenset(
    "\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"
)


def _neutralise_controls(name: str) -> str:
    """Map control characters (Cc), lone surrogates (Cs) and bidi controls to ``_``."""
    return "".join(
        "_" if unicodedata.category(c) in ("Cc", "Cs") or c in _BIDI_CONTROLS else c for c in name
    )


def _split_extension(name: str) -> tuple[str, str]:
    """Split off ``.ext`` (the part from the last ``.``) when it is at most 16 characters."""
    dot = name.rfind(".")
    if dot > 0 and len(name) - dot - 1 <= _MAX_EXTENSION_CHARS:
        return name[:dot], name[dot:]
    return name, ""


def _cut_utf8(name: str, limit: int) -> str:
    """At most ``limit`` UTF-8 bytes, cut at a character boundary, extension kept."""
    if len(name.encode("utf-8")) <= limit:
        return name
    stem, ext = _split_extension(name)
    budget = limit - len(ext.encode("utf-8"))
    return stem.encode("utf-8")[:budget].decode("utf-8", "ignore") + ext


def _cut_chars(name: str, limit: int) -> str:
    if len(name) <= limit:
        return name
    stem, ext = _split_extension(name)
    return stem[: limit - len(ext)] + ext


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
    return _cut_chars(fallback, _MAX_FALLBACK_CHARS)


def content_disposition(filename: str, disposition: str = "attachment") -> str:
    """Return ``<disposition>; filename="<ascii>"; filename*=UTF-8''<encoded>``."""
    name = _cut_utf8(_neutralise_controls(filename), _MAX_NAME_BYTES)
    encoded = quote(name, safe="")
    return f"{disposition}; filename=\"{_ascii_fallback(name)}\"; filename*=UTF-8''{encoded}"
