"""TC-008.10 (real DB): migration 0010 converts legacy field values to the identified envelope.

SR-022 AC 7 (no existing value becomes unreadable), TASK-194, ADR-0018. Rows are written in the
format that existed before TASK-193 (``base64url(nonce || ciphertext)``, no prefix, no associated
data), built here independently of the application code with ``AESGCM``.
"""

from __future__ import annotations

import base64
import os
import threading
import uuid
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from alembic import command
from alembic.config import Config
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pydantic import SecretStr
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from testcontainers.postgres import PostgresContainer

import app.db.crypto as crypto_mod
from app.db.crypto import decrypt, encrypt
from postgres_image import POSTGRES_IMAGE

_DOCKER_SOCKET = os.path.expanduser("~/.docker/run/docker.sock")
if os.path.exists(_DOCKER_SOCKET) and not os.environ.get("DOCKER_HOST"):
    os.environ["DOCKER_HOST"] = f"unix://{_DOCKER_SOCKET}"

_BACKEND_DIR = Path(__file__).parent.parent.parent
_KID = "k2"


def _key() -> bytes:
    return os.urandom(32)


def _b64(key: bytes) -> str:
    return base64.urlsafe_b64encode(key).decode()


def legacy_encrypt(plaintext: str, key: bytes) -> str:
    """The pre-TASK-193 format: base64url(nonce || AES-GCM(key, nonce, plaintext)), no AAD."""
    nonce = os.urandom(12)
    return base64.urlsafe_b64encode(
        nonce + AESGCM(key).encrypt(nonce, plaintext.encode(), None)
    ).decode()


def legacy_decrypt(value: str, key: bytes) -> str:
    raw = base64.urlsafe_b64decode(value.encode())
    return AESGCM(key).decrypt(raw[:12], raw[12:], None).decode()


@pytest.fixture(scope="module")
def pg_url() -> Iterator[str]:
    with PostgresContainer(POSTGRES_IMAGE) as container:
        url = container.get_connection_url()
        cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
        cfg.set_main_option("script_location", str(_BACKEND_DIR / "app" / "db" / "alembic"))
        cfg.set_main_option("sqlalchemy.url", url)
        command.upgrade(cfg, "0009")
        yield url


@pytest.fixture
def cfg(pg_url: str) -> Config:
    c = Config(str(_BACKEND_DIR / "alembic.ini"))
    c.set_main_option("script_location", str(_BACKEND_DIR / "app" / "db" / "alembic"))
    c.set_main_option("sqlalchemy.url", pg_url)
    return c


@pytest.fixture
def engine(pg_url: str, cfg: Config) -> Iterator[Engine]:
    eng = create_engine(pg_url)
    with eng.begin() as conn:
        conn.execute(text("TRUNCATE clinical_entry CASCADE"))
        conn.execute(text("ALTER TABLE clinical_entry ALTER COLUMN description SET NOT NULL"))
    command.stamp(cfg, "0009")
    yield eng
    eng.dispose()


@pytest.fixture
def key(monkeypatch: pytest.MonkeyPatch) -> bytes:
    """The current key, id ``k2``, as the migration and the application read it."""
    k = _key()
    settings = MagicMock()
    settings.at_rest_encryption_key = SecretStr(_b64(k))
    settings.at_rest_encryption_key_id = _KID
    settings.at_rest_encryption_retired_keys = None
    monkeypatch.setattr(crypto_mod, "get_settings", lambda: settings)
    return k


def _insert(engine: Engine, values: list[str | None]) -> list[uuid.UUID]:
    ids = [uuid.uuid4() for _ in values]
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL session_replication_role = replica"))  # no FK rows needed
        conn.execute(
            text(
                "INSERT INTO clinical_entry (id, patient_id, author_doctor_id, occurred_at, "
                "description) VALUES (:id, gen_random_uuid(), gen_random_uuid(), now(), :d)"
            ),
            [{"id": i, "d": v} for i, v in zip(ids, values, strict=True)],
        )
    return ids


def _stored(engine: Engine) -> dict[uuid.UUID, str | None]:
    with engine.connect() as conn:
        return {
            r.id: r.description
            for r in conn.execute(text("SELECT id, description FROM clinical_entry"))
        }


def test_legacy_rows_become_identified_and_read_back(engine, cfg, key):
    plaintexts = [f"entry {n} é中 {'x' * n}" for n in range(1, 8)]
    ids = _insert(engine, [legacy_encrypt(p, key) for p in plaintexts])

    command.upgrade(cfg, "0010")

    stored = _stored(engine)
    for row_id, plaintext in zip(ids, plaintexts, strict=True):
        assert stored[row_id].startswith(f"mh1:{_KID}:")
        assert decrypt(stored[row_id]) == plaintext
    # and through the ORM read path the application uses
    from app.db.types import EncryptedString

    assert EncryptedString().process_result_value(stored[ids[0]], None) == plaintexts[0]


def test_identified_rows_are_untouched(engine, cfg, key):
    envelope = encrypt("already identified")
    [mh_id, legacy_id] = _insert(engine, [envelope, legacy_encrypt("old", key)])

    command.upgrade(cfg, "0010")

    stored = _stored(engine)
    assert stored[mh_id] == envelope  # byte-identical, not re-encrypted
    assert decrypt(stored[legacy_id]) == "old"


def test_rerun_converts_nothing_and_changes_no_value(engine, cfg, key):
    _insert(engine, [legacy_encrypt(f"v{n}", key) for n in range(5)])
    command.upgrade(cfg, "0010")
    first = _stored(engine)

    command.stamp(cfg, "0009")  # run the revision again
    command.upgrade(cfg, "0010")

    assert _stored(engine) == first


def test_empty_table_is_a_no_op_and_needs_no_key_settings(engine, cfg, monkeypatch):
    def refuse():
        raise AssertionError("key settings must not be read when there is nothing to convert")

    monkeypatch.setattr(crypto_mod, "get_settings", refuse)
    command.upgrade(cfg, "0010")
    assert _stored(engine) == {}


def test_value_under_another_key_stops_the_migration_with_no_partial_conversion(engine, cfg, key):
    secret = "patient has a very specific diagnosis"
    good = [legacy_encrypt(f"ok {n}", key) for n in range(3)]
    bad = legacy_encrypt(secret, _key())
    values = [*good, bad]
    ids = _insert(engine, values)
    before = _stored(engine)

    with pytest.raises(Exception) as excinfo:
        command.upgrade(cfg, "0010")

    message = str(excinfo.value)
    assert str(ids[3]) in message and "1 clinical_entry.description" in message
    for forbidden in [secret, bad, *good]:
        assert forbidden not in message
    assert _stored(engine) == before  # every row still legacy and byte-identical


def test_every_undecryptable_row_is_named(engine, cfg, key):
    other = _key()
    ids = _insert(
        engine, [legacy_encrypt("a", key), legacy_encrypt("b", other), legacy_encrypt("c", other)]
    )
    with pytest.raises(Exception) as excinfo:
        command.upgrade(cfg, "0010")
    message = str(excinfo.value)
    assert "2 clinical_entry.description" in message
    assert str(ids[1]) in message and str(ids[2]) in message and str(ids[0]) not in message


def test_failure_during_conversion_rolls_back_every_row(engine, cfg, key, monkeypatch):
    """Pass 1 passes, then the write path fails halfway: the transaction leaves no row converted."""
    ids = _insert(engine, [legacy_encrypt(f"v{n}", key) for n in range(6)])
    before = _stored(engine)
    calls = {"n": 0}
    real = crypto_mod.encrypt

    def flaky(value: str) -> str:
        calls["n"] += 1
        if calls["n"] == 4:
            raise RuntimeError("simulated crash")
        return real(value)

    monkeypatch.setattr(crypto_mod, "encrypt", flaky)
    with pytest.raises(Exception, match="simulated crash"):
        command.upgrade(cfg, "0010")

    assert calls["n"] == 4
    assert _stored(engine) == before
    assert all(not v.startswith("mh1:") for v in _stored(engine).values())
    assert len(ids) == 6


def test_null_empty_plaintext_and_raw_empty_value(engine, cfg, key):
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE clinical_entry ALTER COLUMN description DROP NOT NULL"))
    null_id, empty_plain_id = _insert(engine, [None, legacy_encrypt("", key)])

    command.upgrade(cfg, "0010")

    stored = _stored(engine)
    assert stored[null_id] is None  # NULL is left alone
    assert decrypt(stored[empty_plain_id]) == ""

    # a raw empty string was never written by the application and cannot be read: refuse, name it
    command.stamp(cfg, "0009")
    [raw_empty_id] = _insert(engine, [""])
    with pytest.raises(Exception) as excinfo:
        command.upgrade(cfg, "0010")
    assert str(raw_empty_id) in str(excinfo.value)
    assert _stored(engine)[raw_empty_id] == ""


def test_large_batch_spans_several_batches(engine, cfg, key):
    count = 1300  # 500 + 500 + 300
    plaintexts = [f"row {n}" for n in range(count)]
    ids = _insert(engine, [legacy_encrypt(p, key) for p in plaintexts])

    command.upgrade(cfg, "0010")

    stored = _stored(engine)
    assert len(stored) == count
    assert all(decrypt(stored[i]) == p for i, p in zip(ids, plaintexts, strict=True))
    assert all(v.startswith(f"mh1:{_KID}:") for v in stored.values())


def test_large_batch_with_a_bad_row_in_the_last_batch_converts_nothing(engine, cfg, key):
    values = [legacy_encrypt(f"row {n}", key) for n in range(1100)]
    ids = _insert(engine, values)
    with engine.begin() as conn:  # corrupt the row with the highest id (the last batch)
        last = max(ids)
        conn.execute(
            text("UPDATE clinical_entry SET description = :d WHERE id = :i"),
            {"d": "not-valid", "i": last},
        )
    before = _stored(engine)

    with pytest.raises(Exception) as excinfo:
        command.upgrade(cfg, "0010")

    assert str(last) in str(excinfo.value)
    assert _stored(engine) == before


def test_downgrade_returns_to_the_unprefixed_format_with_the_same_plaintext(engine, cfg, key):
    plaintexts = ["one", "", "tres é"]
    ids = _insert(engine, [encrypt(p) for p in plaintexts])
    command.stamp(cfg, "0010")

    command.downgrade(cfg, "0009")

    stored = _stored(engine)
    for row_id, plaintext in zip(ids, plaintexts, strict=True):
        assert not stored[row_id].startswith("mh1:")
        assert legacy_decrypt(stored[row_id], key) == plaintext
    # and the round trip returns to the identified format
    command.upgrade(cfg, "0010")
    assert all(
        decrypt(v) == p for v, p in zip((_stored(engine)[i] for i in ids), plaintexts, strict=True)
    )


def test_downgrade_refuses_a_value_under_a_retired_key_and_changes_nothing(
    engine, cfg, key, monkeypatch
):
    old = _key()
    old_settings = MagicMock()
    old_settings.at_rest_encryption_key = SecretStr(_b64(old))
    old_settings.at_rest_encryption_key_id = "k1"
    old_settings.at_rest_encryption_retired_keys = None
    monkeypatch.setattr(crypto_mod, "get_settings", lambda: old_settings)
    retired_value = encrypt("under the old key")
    new_settings = MagicMock()
    new_settings.at_rest_encryption_key = SecretStr(_b64(key))
    new_settings.at_rest_encryption_key_id = _KID
    new_settings.at_rest_encryption_retired_keys = SecretStr(f"k1:{_b64(old)}")
    monkeypatch.setattr(crypto_mod, "get_settings", lambda: new_settings)
    [retired_id, current_id] = _insert(engine, [retired_value, encrypt("current")])
    command.stamp(cfg, "0010")
    before = _stored(engine)

    with pytest.raises(Exception) as excinfo:
        command.downgrade(cfg, "0009")

    assert str(retired_id) in str(excinfo.value) and str(current_id) not in str(excinfo.value)
    assert _stored(engine) == before


# Plaintexts that a normalising or trimming conversion would change. Inserted directly, not through
# the API (which strips the text, ClinicalService.create_entry), and compared as bytes.
_TRICKY = [
    "trailing space   ",
    "   leading space",
    "\ttab\t",
    "line1\nline2\n",
    "crlf\r\nline\r\n",
    "\n",
    " ",
    "nul\x00inside",
    "e\u0301 decomposed (NFD) vs \u00e9",
    "\u202eRTL override\u202c",
    "\U0001f600\U0001f9ec emoji \u4e2d\u6587 \u0627\u0644\u0639\u0631\u0628\u064a\u0629",
    "zero\u200bwidth\ufeffbom",
    "x" * 200_000,
    "mh1:k2:literal prefix in plaintext",
    "%_\\ like metacharacters /",
]


def _assert_bytes(engine: Engine, ids: list[uuid.UUID]) -> None:
    stored = _stored(engine)
    for row_id, plaintext in zip(ids, _TRICKY, strict=True):
        assert stored[row_id].startswith(f"mh1:{_KID}:")
        assert decrypt(stored[row_id]).encode() == plaintext.encode(), repr(plaintext[:30])


def test_plaintext_is_preserved_byte_for_byte_through_upgrade_downgrade_upgrade(engine, cfg, key):
    ids = _insert(engine, [legacy_encrypt(p, key) for p in _TRICKY])

    command.upgrade(cfg, "0010")
    _assert_bytes(engine, ids)

    command.downgrade(cfg, "0009")
    stored = _stored(engine)
    for row_id, plaintext in zip(ids, _TRICKY, strict=True):
        assert legacy_decrypt(stored[row_id], key).encode() == plaintext.encode()

    command.upgrade(cfg, "0010")
    _assert_bytes(engine, ids)


def test_migration_holds_a_table_lock_that_blocks_writers_but_not_readers(
    engine, cfg, key, pg_url, monkeypatch
):
    """While 0010 converts, an INSERT waits for the lock (times out here); a SELECT is served."""
    _insert(engine, [legacy_encrypt(f"v{n}", key) for n in range(700)])
    gate, started = threading.Event(), threading.Event()
    real, calls = crypto_mod.encrypt, {"n": 0}

    def hold(value: str) -> str:
        calls["n"] += 1
        if calls["n"] == 600:  # inside the second batch, the first one already updated
            started.set()
            gate.wait(30)
        return real(value)

    monkeypatch.setattr(crypto_mod, "encrypt", hold)
    errors: list[BaseException] = []

    def run() -> None:
        try:
            command.upgrade(cfg, "0010")
        except BaseException as exc:  # noqa: BLE001 - reported by the assertion below
            errors.append(exc)

    worker = threading.Thread(target=run)
    worker.start()
    other = create_engine(pg_url)
    try:
        assert started.wait(60), "the migration did not reach the second batch"
        with other.connect() as conn:
            conn.execute(text("SET statement_timeout = '3s'"))  # a blocked reader fails fast
            rows = conn.execute(text("SELECT description FROM clinical_entry")).all()
            assert len(rows) == 700  # a reader is not blocked (and sees the uncommitted state)
        with other.connect() as conn:
            conn.execute(text("SET lock_timeout = '1s'"))
            with pytest.raises(OperationalError, match="lock timeout"):
                conn.execute(
                    text(
                        "INSERT INTO clinical_entry (id, patient_id, author_doctor_id, "
                        "occurred_at, description) VALUES (gen_random_uuid(), "
                        "gen_random_uuid(), gen_random_uuid(), now(), 'x')"
                    )
                )
    finally:
        gate.set()
        worker.join(60)
        other.dispose()
    assert not errors
    assert all(v.startswith(f"mh1:{_KID}:") for v in _stored(engine).values())
