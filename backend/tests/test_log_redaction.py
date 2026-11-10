"""TASK-138: the redaction filter (SR-043 AC 2, AC 3), through the real configured handler."""

from __future__ import annotations

import io
import json
import logging
import sys
import time
import uuid
from collections.abc import Iterator

import pytest

from app.core.logging import EMAIL_PLACEHOLDER, RedactionFilter, configure_logging, redact_text

ADDRESS = "a.person@example.org"


@pytest.fixture
def stream(monkeypatch: pytest.MonkeyPatch) -> Iterator[io.StringIO]:
    """Root handler of configure_logging() writing to a buffer; root logger restored after."""
    root = logging.getLogger()
    saved = (root.handlers[:], root.level)
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)
    monkeypatch.setattr(logging.root.manager, "disable", logging.NOTSET)
    # Other tests (Alembic's fileConfig) can leave existing loggers disabled.
    reenabled = [
        lg
        for lg in logging.Logger.manager.loggerDict.values()
        if isinstance(lg, logging.Logger) and lg.disabled
    ]
    for lg in reenabled:
        lg.disabled = False
    configure_logging()
    yield buffer
    root.handlers, root.level = saved[0], saved[1]
    for lg in reenabled:
        lg.disabled = True


def _records(buffer: io.StringIO) -> list[dict]:
    return [json.loads(line) for line in buffer.getvalue().splitlines() if line.strip()]


def test_extra_field_under_an_arbitrary_name_is_redacted(stream) -> None:
    """SR-043 AC 3: an address in a field with an arbitrary name never reaches the log."""
    logging.getLogger("app.test").info("hello", extra={"anything_at_all": ADDRESS})
    assert ADDRESS not in stream.getvalue()
    assert _records(stream)[0]["extra"]["anything_at_all"] == EMAIL_PLACEHOLDER


def test_message_args_and_nested_values_are_redacted(stream) -> None:
    """SR-043 AC 2: message, %s args and nested dict/list values."""
    log = logging.getLogger("app.test")
    log.info(f"sent to {ADDRESS}")
    log.info("sent to %s", ADDRESS)
    log.info("sent to %(who)s", {"who": ADDRESS})
    log.info("nested", extra={"opaque": {"a": [{"b": (ADDRESS,)}], ADDRESS: 1}})
    log.info("percent-encoded", extra={"url": "/x?email=a.person%40example.org"})
    assert "a.person" not in stream.getvalue()
    assert "example.org" not in stream.getvalue()


def test_exception_text_and_traceback_are_redacted(stream) -> None:
    """SR-043 AC 2/3: an address in exception text, in the message and in the traceback."""
    log = logging.getLogger("app.test")
    try:
        raise ValueError(f"cannot deliver to {ADDRESS}")
    except ValueError:
        log.exception("delivery failed")
        log.error("failed: %s", ValueError(ADDRESS), exc_info=True)
    assert ADDRESS not in stream.getvalue()
    assert EMAIL_PLACEHOLDER in stream.getvalue()


def test_personal_and_credential_fields_are_redacted_by_name(stream) -> None:
    """SR-043 AC 1/2: names, date of birth, clinical text, tokens and task arguments."""
    logging.getLogger("app.test").info(
        "task",
        extra={
            "first_name": "Ada",
            "surname": "Lovelace",
            "date_of_birth": "1815-12-10",
            "description": "chronic migraine",
            "data": {"args": ["x", "RETRIEVAL-CODE"], "kwargs": {"activation_token": "TOK-1"}},
        },
    )
    out = stream.getvalue()
    for secret in ("Ada", "Lovelace", "1815-12-10", "migraine", "RETRIEVAL-CODE", "TOK-1"):
        assert secret not in out


def test_identifiers_survive(stream) -> None:
    """SR-043 AC 1: a UUID and an account id are kept so operators can correlate."""
    account_id, dataset = str(uuid.uuid4()), uuid.uuid4()
    logging.getLogger("app.test").info(
        "ok %s", dataset, extra={"account_id": account_id, "erased": 3, "ts": "2026-11-02T10:00"}
    )
    record = _records(stream)[0]
    assert str(dataset) in record["message"]
    assert record["extra"] == {"account_id": account_id, "erased": 3, "ts": "2026-11-02T10:00"}


def test_malformed_format_string_does_not_leak_or_raise(stream) -> None:
    """SR-043 AC 2: a bad %-format is emitted without its arguments."""
    logging.getLogger("app.test").info("bad %d", ADDRESS)
    assert ADDRESS not in stream.getvalue()


def test_every_handler_gets_the_filter_including_non_propagating_loggers(stream) -> None:
    """SR-043 AC 2: the root handler and the handlers of loggers that do not propagate."""
    own = logging.getLogger("uvicorn.test_task138")
    own.propagate = False
    handler = logging.StreamHandler(io.StringIO())
    own.addHandler(handler)
    try:
        configure_logging()
        configure_logging()  # idempotent
        assert [type(f) for f in handler.filters] == [RedactionFilter]
        own.warning("to %s", ADDRESS)
        assert ADDRESS not in handler.stream.getvalue()
        assert [type(f) for f in logging.getLogger().handlers[0].filters] == [RedactionFilter]
    finally:
        own.removeHandler(handler)


def test_filter_is_what_redacts(stream) -> None:
    """Negative control inside the suite: without the filter the address does reach the stream."""
    for h in logging.getLogger().handlers:
        h.filters.clear()
    logging.getLogger("app.test").info("hello", extra={"anything_at_all": ADDRESS})
    assert ADDRESS in stream.getvalue()


# --- QA round 1 (TASK-138 findings 1 to 5) ---

_TIMING_BOUND = (
    0.05  # seconds; the unfixed expression needs 0.09 s for 4 KB and does not finish for 1 MB
)


def _seconds(text: str) -> float:
    from app.core.logging import redact_text  # noqa: PLC0415

    started = time.perf_counter()
    redact_text(text)
    return time.perf_counter() - started


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("x" * 1_000_000, id="1MB-no-at"),
        pytest.param("a" * 100_000 + "@!", id="100k-then-at"),
        pytest.param(
            "GET /api/v1/" + "a1b2c3d4" * 500 + "?q=" + "z" * 90 + " HTTP/1.1",
            id="4KB-request-line",
        ),
        pytest.param("GET /" + "a1b2" * 1000 + "@x HTTP/1.1", id="4KB-with-at"),
        pytest.param("a@" * 50_000, id="repeated-at"),
        pytest.param("%40" * 30_000, id="repeated-percent-40"),
    ],
)
def test_redaction_runs_in_linear_time(text: str) -> None:
    """SR-043 AC 2 (finding 1): long text without an address does not block the logging caller."""
    assert _seconds(text) < _TIMING_BOUND


def test_a_long_message_with_an_address_is_still_redacted_quickly() -> None:
    text = "x" * 200_000 + " mail " + ADDRESS + " " + "y" * 200_000
    started = time.perf_counter()
    out = redact_text(text)
    assert time.perf_counter() - started < _TIMING_BOUND
    assert ADDRESS not in out and EMAIL_PLACEHOLDER in out


@pytest.mark.parametrize(
    ("raw", "hidden"),
    [
        ("to jöhn.dœ@example.org now", "dœ"),
        ("to ada@bücher.de now", "bücher"),
        ("to ada@例え.テスト now", "例え"),
        ("to ada%2Btag%40example.org now", "ada"),
        ("to ada@xn--bcher-kva.de now", "xn--"),
        ("to ADA.Lovelace+x@Example.ORG now", "Lovelace"),
    ],
)
def test_unicode_idn_and_percent_encoded_addresses_are_redacted(raw: str, hidden: str) -> None:
    """SR-043 AC 2 (finding 4): the whole address goes, nothing of it is left in front."""
    assert redact_text(raw) == f"to {EMAIL_PLACEHOLDER} now"
    assert hidden not in redact_text(raw)


def test_celery_node_name_with_a_container_id_is_kept() -> None:
    """Finding 4 note: ``celery@<container-id>`` has no dotted domain and is not an address."""
    assert redact_text("celery@3f9a1c2b7d10 ready") == "celery@3f9a1c2b7d10 ready"


class _Unprintable:
    def __str__(self) -> str:
        raise RuntimeError("no text for you")


def test_extra_whose_str_raises_does_not_raise_or_lose_the_record(stream) -> None:
    """SR-043 AC 2 (finding 3): the filter never raises into the caller."""
    logging.getLogger("app.test").info("kept", extra={"thing": _Unprintable()})
    record = _records(stream)[0]
    assert record["message"] == "kept"
    assert "RuntimeError" not in stream.getvalue()


def test_self_referencing_and_very_deep_values_are_cut_not_raised(stream) -> None:
    """SR-043 AC 2 (finding 3): a cycle and 10 000 levels of nesting."""
    cycle: dict = {"a": 1}
    cycle["self"] = cycle
    deep: list = []
    for _ in range(10_000):
        deep = [deep]
    log = logging.getLogger("app.test")
    log.info("cycle", extra={"c": cycle})
    log.info("deep", extra={"d": deep, "email_like": ADDRESS})
    records = _records(stream)
    assert [r["message"] for r in records] == ["cycle", "deep"]
    assert ADDRESS not in stream.getvalue()


def test_a_failure_inside_the_filter_fails_closed_and_keeps_the_record(
    stream, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SR-043 AC 2 (finding 3): if redaction itself fails, no argument or extra is emitted."""
    import app.core.logging as module  # noqa: PLC0415

    def boom(_value: object, *_a: object) -> object:
        raise ValueError("boom")

    monkeypatch.setattr(module, "redact_value", boom)
    logging.getLogger("app.test").info("sent to %s", ADDRESS, extra={"field": ADDRESS})
    out = stream.getvalue()
    assert ADDRESS not in out
    record = _records(stream)[0]
    assert record["message"] == "[log record could not be redacted: ValueError]"
    assert "extra" not in record


def test_non_string_dict_keys_do_not_drop_the_record(stream) -> None:
    """Finding 5: bytes, tuple and address keys become redacted strings."""
    logging.getLogger("app.test").info("keys", extra={"d": {b"k": 1, (1, 2): 2, ADDRESS: 3, 7: 4}})
    record = _records(stream)[0]
    assert set(record["extra"]["d"]) == {"b'k'", "(1, 2)", EMAIL_PLACEHOLDER, "7"}


def test_failed_insert_with_personal_data_does_not_reach_the_log(
    stream, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SR-043 AC 1 (finding 2): the application engine hides bound parameters, so the
    IntegrityError text logged by the 500 handler holds no name. The log call is reproduced from
    ``app/api/errors.py`` (``logger.exception("Unhandled exception for %s %s", ...)``)."""
    import sqlalchemy as sa  # noqa: PLC0415
    from sqlalchemy.exc import IntegrityError  # noqa: PLC0415

    import app.db.repositories.session as session_module  # noqa: PLC0415

    settings = type("S", (), {"database_url": "sqlite://"})()
    monkeypatch.setattr(session_module, "get_settings", lambda: settings)
    engine = session_module.get_engine.__wrapped__()
    meta = sa.MetaData()
    accounts = sa.Table(
        "accounts",
        meta,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("first_name", sa.String, nullable=False),
        sa.Column("surname", sa.String, unique=True),
    )
    meta.create_all(engine)
    # Built at run time: a traceback prints source lines, and a literal here would be one.
    values = {"first_name": "".join(["Ad", "a"]), "surname": "".join(["Love", "lace"])}
    with engine.begin() as conn:
        conn.execute(sa.insert(accounts).values(**values))
    log = logging.getLogger("app.api.errors")
    try:
        with engine.begin() as conn:
            conn.execute(sa.insert(accounts).values(**values))
    except IntegrityError:
        log.exception("Unhandled exception for %s %s", "POST", "/api/v1/accounts")
    out = stream.getvalue()
    assert "IntegrityError" in out  # the failure was logged
    assert "Ada" not in out and "Lovelace" not in out


class _BrokenMapping(dict):
    def items(self):  # type: ignore[no-untyped-def,override]
        raise RuntimeError("cannot iterate")


def test_extra_that_breaks_the_walk_is_dropped_not_raised(stream) -> None:
    """SR-043 AC 2 (finding 3): a value that raises while it is walked is handled by the
    fail-closed branch of the filter (the unprintable object above is handled one layer lower)."""
    logging.getLogger("app.test").info("kept", extra={"thing": _BrokenMapping(a=ADDRESS)})
    record = _records(stream)[0]
    assert record["message"] == "[log record could not be redacted: RuntimeError]"
    assert ADDRESS not in stream.getvalue() and "extra" not in record
