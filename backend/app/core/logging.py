"""Structured JSON logging configuration.

Emits logs to stdout as JSON objects. Never logs PHI or credentials (SR-043): a
``RedactionFilter`` sits on every handler and replaces email-shaped values, personal-data fields
and task arguments before a record is formatted.
"""

import json
import logging
import re
import sys
from typing import Any

EMAIL_PLACEHOLDER = "[REDACTED-EMAIL]"
FIELD_PLACEHOLDER = "[REDACTED]"

# Email-shaped values (SR-043 AC 2), Unicode and IDN included. The start is anchored, so each run
# of local-part characters is tried once, and every part is bounded: the cost is linear in the text
# (a bare ``[\w.]+@`` restarts at every position and is quadratic). The local part allows ``%XX``
# so an address inside a URL (``ada%2Btag%40example.org``) is taken whole. Accepted limits: a local
# part over 64 characters (invalid per RFC 5321), quoted local parts, IP-literal and single-label
# domains are not matched. ``celery@host.example`` (dotted node name) is matched;
# ``celery@<container-id>`` is not.
_EMAIL = re.compile(
    r"(?<![\w.+%'\-])"
    r"(?:[\w.+'\-]|%[0-9A-Fa-f]{2}){1,64}"
    r"(?:@|%40)"
    r"(?:[^\W_][\w\-]{0,62}\.){1,126}(?:[^\W\d_]{2,63}|xn--[\w\-]{1,59})"
)
_MAX_DEPTH = 20
_FAILED = "[log record could not be redacted: {}]"

# Field names (case-insensitive substring) whose value is personal data, a clinical free text or
# a credential: the value is replaced whatever it contains.
_SENSITIVE_KEY_PARTS = (
    "email",
    "recipient",
    "first_name",
    "last_name",
    "full_name",
    "surname",
    "birth",
    "dob",
    "phone",
    "diagnos",
    "clinical",
    "description",
    "note",
    "password",
    "secret",
    "token",
    "retrieval_code",
)
# Celery's task-failure and retry records carry the task arguments (activation tokens, addresses).
_ARGUMENT_KEYS = frozenset({"args", "kwargs", "argsrepr", "kwargsrepr"})

_STANDARD_ATTRIBUTES = frozenset(
    set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime", "taskName"}
)
_SCALARS = (int, float, bool, type(None))


def _sensitive_key(key: object) -> bool:
    name = str(key).lower()
    return name in _ARGUMENT_KEYS or any(part in name for part in _SENSITIVE_KEY_PARTS)


def _safe_text(value: object) -> str:
    """``str(value)``, then ``repr``, then a fixed label: never raises."""
    try:
        return str(value)
    except Exception:  # noqa: BLE001
        try:
            return repr(value)
        except Exception:  # noqa: BLE001
            return f"<unprintable {type(value).__name__}>"


def redact_text(text: str) -> str:
    """Replace every email-shaped value in ``text``."""
    if "@" not in text and "%40" not in text:
        return text
    return _EMAIL.sub(EMAIL_PLACEHOLDER, text)


def redact_value(value: Any, _depth: int = 0, _path: frozenset[int] = frozenset()) -> Any:
    """Redact a structured value. Containers are walked (depth-limited, cycle-safe); any other
    object is replaced by its redacted text, so a later ``str()`` cannot raise or reveal."""
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, _SCALARS):
        return value
    if _depth >= _MAX_DEPTH or id(value) in _path:
        return FIELD_PLACEHOLDER
    path = _path | {id(value)}
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            key = redact_text(_safe_text(k))
            out[key] = FIELD_PLACEHOLDER if _sensitive_key(k) else redact_value(v, _depth + 1, path)
        return out
    if isinstance(value, list | tuple | set | frozenset):
        return [redact_value(v, _depth + 1, path) for v in value]
    return redact_text(_safe_text(value))


def custom_attributes(record: logging.LogRecord) -> dict[str, Any]:
    """The fields a caller added with ``extra=``, under any name."""
    return {k: v for k, v in record.__dict__.items() if k not in _STANDARD_ATTRIBUTES}


class RedactionFilter(logging.Filter):
    """SR-043 AC 2: redact the message, the arguments, every extra field and exception text.

    It never raises and never drops a record: if redaction fails, the record is emitted with a
    fixed message and without its arguments, extra fields and exception text (fail closed).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            self._redact(record)
        except Exception as exc:  # noqa: BLE001
            record.msg = _FAILED.format(type(exc).__name__)
            record.args = None
            for key in custom_attributes(record):
                delattr(record, key)
            record.exc_info = record.exc_text = record.stack_info = None
        return True

    @staticmethod
    def _redact(record: logging.LogRecord) -> None:
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001 - a malformed format string must not leak its arguments
            message = _safe_text(record.msg)
        record.msg = redact_text(message)
        record.args = None
        for key, value in custom_attributes(record).items():
            setattr(record, key, FIELD_PLACEHOLDER if _sensitive_key(key) else redact_value(value))
        if record.exc_info and not record.exc_text:
            record.exc_text = logging.Formatter().formatException(record.exc_info)
        if record.exc_text:
            record.exc_text = redact_text(record.exc_text)
        if record.stack_info:
            record.stack_info = redact_text(record.stack_info)


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        extra = custom_attributes(record)
        if extra:
            log_record["extra"] = extra
        if record.exc_info:
            log_record["exc_info"] = record.exc_text or self.formatException(record.exc_info)
        return json.dumps(log_record, default=_safe_text)


def _attach_filter(handler: logging.Handler) -> None:
    if not any(isinstance(f, RedactionFilter) for f in handler.filters):
        handler.addFilter(RedactionFilter())


def configure_logging() -> None:
    """Configure root logger to emit structured JSON to stdout, with redaction on every handler.

    Called by the API lifespan, and by the worker and scheduler through Celery's
    ``setup_logging`` signal.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    # Loggers that keep their own handlers (uvicorn, gunicorn) get the same filter.
    for existing in (root, *logging.Logger.manager.loggerDict.values()):
        if isinstance(existing, logging.Logger):
            for h in existing.handlers:
                _attach_filter(h)
