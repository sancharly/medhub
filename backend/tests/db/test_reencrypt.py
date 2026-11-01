"""TC-008.11 (real DB): the key-rotation command ``python -m app.db.reencrypt``.

SR-022 AC 8 (a documented rotation), AC 6 and AC 7 (values stay readable), ADR-0018, TASK-195.
Rows are written through ``crypto.encrypt`` under the key that is configured at that moment, so a
rotation here is: write under k1, change the settings (current k2, retired k1), run the command.
"""

from __future__ import annotations

import base64
import io
import os
import threading
import time
import uuid
from collections.abc import Callable, Iterator
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from pydantic import SecretStr
from sqlalchemy import Engine, MetaData, create_engine, text
from sqlalchemy.exc import OperationalError

import app.db.crypto as crypto_mod
import app.db.reencrypt as reencrypt
from app.db.crypto import decrypt, encrypt
from app.db.reencrypt import (
    EXIT_OK,
    EXIT_PENDING,
    EXIT_REFUSED,
    Column,
    ReencryptError,
    discover,
    verify_key_ids,
)
from app.db.types import EncryptedString

KEYS = {name: os.urandom(32) for name in ("k1", "k2", "k3", "k9")}


def _b64(key: bytes) -> str:
    return base64.urlsafe_b64encode(key).decode()


@pytest.fixture
def configure(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """``configure("k2", "k1")``: current key id, then the retired key ids (from ``KEYS``)."""

    def _configure(current: str, *retired: str) -> None:
        settings = MagicMock()
        settings.at_rest_encryption_key = SecretStr(_b64(KEYS[current]))
        settings.at_rest_encryption_key_id = current
        settings.at_rest_encryption_retired_keys = (
            SecretStr(",".join(f"{r}:{_b64(KEYS[r])}" for r in retired)) if retired else None
        )
        monkeypatch.setattr(crypto_mod, "get_settings", lambda: settings)

    return _configure


@pytest.fixture
def engine(pg_engine: Engine) -> Iterator[Engine]:
    with pg_engine.begin() as conn:
        conn.execute(text("TRUNCATE clinical_entry CASCADE"))
    yield pg_engine


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


def _seed(engine: Engine, configure, kid: str, plaintexts: list[str]) -> list[uuid.UUID]:
    configure(kid)
    return _insert(engine, [encrypt(p) for p in plaintexts])


def _kids(engine: Engine) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in _stored(engine).values():
        if value is not None:
            kid = value.split(":", 2)[1]
            counts[kid] = counts.get(kid, 0) + 1
    return counts


def _assert_plaintexts(engine: Engine, ids: list[uuid.UUID], plaintexts: list[str | None]) -> None:
    stored = _stored(engine)
    for row_id, plaintext in zip(ids, plaintexts, strict=True):
        value = stored[row_id]
        if plaintext is None:
            assert value is None
        else:
            assert decrypt(value).encode() == plaintext.encode(), repr(plaintext[:30])


def _run(engine: Engine, *argv: str) -> tuple[int, str]:
    out = io.StringIO()
    if argv[0] == "--check":
        return reencrypt.check(engine, out=out), out.getvalue()
    return reencrypt.apply(engine, out=out), out.getvalue()


# ----- discovery -------------------------------------------------------------------------------


def test_discovery_finds_every_encrypted_string_column_of_the_models():
    assert discover() == [Column("clinical_entry", "id", "description")]


def test_discovery_covers_a_future_column_without_a_change_to_the_command():
    metadata = MetaData()
    sa.Table(
        "later",
        metadata,
        sa.Column("pk", sa.Integer, primary_key=True),
        sa.Column("secret", EncryptedString()),
        sa.Column("plain", sa.String),
    )
    assert discover(metadata) == [Column("later", "pk", "secret")]
    sa.Table(
        "composite",
        metadata,
        sa.Column("a", sa.Integer, primary_key=True),
        sa.Column("b", sa.Integer, primary_key=True),
        sa.Column("secret", EncryptedString()),
    )
    with pytest.raises(ReencryptError, match="single-column primary key"):
        discover(metadata)


# ----- rotation --------------------------------------------------------------------------------


def test_rotation_k1_to_k2_with_every_value_readable_before_during_and_after(
    engine, configure, monkeypatch
):
    plaintexts = [f"entry {n} é中 {'x' * n}" for n in range(1, 9)]
    ids = _seed(engine, configure, "k1", plaintexts)

    configure("k2", "k1")  # the rotation: new current key, old key retired
    code, report = _run(engine, "--check")
    assert code == EXIT_PENDING and "k1=8" in report
    _assert_plaintexts(engine, ids, plaintexts)  # before

    # during: the second batch fails, the first (3 rows) is committed
    real, calls = crypto_mod.encrypt, {"n": 0}

    def flaky(value: str) -> str:
        calls["n"] += 1
        if calls["n"] == 5:
            raise RuntimeError("simulated crash")
        return real(value)

    monkeypatch.setattr(crypto_mod, "encrypt", flaky)
    with pytest.raises(RuntimeError, match="simulated crash"):
        reencrypt.apply(engine, batch_size=3, out=io.StringIO())
    monkeypatch.setattr(crypto_mod, "encrypt", real)
    assert _kids(engine) == {"k1": 5, "k2": 3}  # mixed
    _assert_plaintexts(engine, ids, plaintexts)
    assert _run(engine, "--check")[0] == EXIT_PENDING

    # resumed: the re-run finishes, no row lost
    code, report = _run(engine, "--apply")
    assert code == EXIT_OK and "converted: 5 value(s)" in report
    assert _kids(engine) == {"k2": 8}
    _assert_plaintexts(engine, ids, plaintexts)  # after
    assert _run(engine, "--check")[0] == EXIT_OK

    # and through the ORM read path the application uses
    assert EncryptedString().process_result_value(_stored(engine)[ids[0]], None) == plaintexts[0]


def test_report_gives_the_counts_per_key_before_and_after(engine, configure):
    _seed(engine, configure, "k1", ["a", "b", "c"])
    configure("k2")
    _insert(engine, [encrypt("d")])
    configure("k2", "k1")

    _, report = _run(engine, "--apply")

    assert "clinical_entry.description before: k1=3, k2=1 (current)" in report
    assert "converted: 3 value(s) in 1 batch(es)" in report
    assert "clinical_entry.description after: k2=4 (current)" in report


def test_rerun_converts_nothing_and_changes_no_value(engine, configure):
    _seed(engine, configure, "k1", [f"v{n}" for n in range(5)])
    configure("k2", "k1")
    _run(engine, "--apply")
    first = _stored(engine)

    code, report = _run(engine, "--apply")

    assert code == EXIT_OK and "converted: 0 value(s) in 0 batch(es)" in report
    assert _stored(engine) == first  # byte-identical: nothing was re-encrypted


def test_null_is_left_alone_and_an_empty_plaintext_converts(engine, configure):
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE clinical_entry ALTER COLUMN description DROP NOT NULL"))
    try:
        configure("k1")
        ids = _insert(engine, [None, encrypt(""), encrypt("x")])
        configure("k2", "k1")

        _run(engine, "--apply")

        _assert_plaintexts(engine, ids, [None, "", "x"])
        assert _kids(engine) == {"k2": 2}
    finally:
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE clinical_entry CASCADE"))
            conn.execute(text("ALTER TABLE clinical_entry ALTER COLUMN description SET NOT NULL"))


# Plaintexts that a normalising or trimming conversion would change (as in TASK-194's test).
_TRICKY = [
    "trailing space   ",
    "   leading space",
    "\ttab\t",
    "line1\nline2\n",
    "crlf\r\nline\r\n",
    "\n",
    " ",
    "nul\x00inside",
    "é decomposed (NFD) vs é",
    "‮RTL override‬",
    "\U0001f600\U0001f9ec emoji 中文 العربية",
    "zero​width﻿bom",
    "x" * 200_000,
    "mh1:k2:literal prefix in plaintext",
    "%_\\ like metacharacters /",
]


def test_plaintext_is_preserved_byte_for_byte(engine, configure):
    ids = _seed(engine, configure, "k1", _TRICKY)
    configure("k2", "k1")

    _run(engine, "--apply")

    assert _kids(engine) == {"k2": len(_TRICKY)}
    _assert_plaintexts(engine, ids, list(_TRICKY))


def test_large_batch_spans_several_batches(engine, configure):
    count = 1300  # 500 + 500 + 300
    plaintexts = [f"row {n}" for n in range(count)]
    ids = _seed(engine, configure, "k1", plaintexts)
    configure("k2", "k1")

    code, report = _run(engine, "--apply")

    assert code == EXIT_OK and "converted: 1300 value(s) in 3 batch(es)" in report
    assert _kids(engine) == {"k2": count}
    _assert_plaintexts(engine, ids, list(plaintexts))


def test_plaintext_unchanged_after_k1_k2_k3_with_k1_removed_only_after_the_k2_conversion(
    engine, configure
):
    plaintexts = [f"patient note {n} é" for n in range(6)]
    ids = _seed(engine, configure, "k1", plaintexts)

    configure("k2", "k1")
    assert _run(engine, "--apply")[0] == EXIT_OK
    assert _kids(engine) == {"k2": 6}

    configure("k2")  # k1 removed: safe, no value names it
    assert _run(engine, "--check")[0] == EXIT_OK
    assert verify_key_ids(engine, out=io.StringIO()) == EXIT_OK
    more = _insert(engine, [encrypt("written under k2")])

    configure("k3", "k2")
    assert _run(engine, "--apply")[0] == EXIT_OK
    assert _kids(engine) == {"k3": 7}
    _assert_plaintexts(engine, ids + more, [*plaintexts, "written under k2"])

    configure("k3")  # k2 removed after its conversion
    assert _run(engine, "--check")[0] == EXIT_OK
    _assert_plaintexts(engine, ids + more, [*plaintexts, "written under k2"])


# ----- refusal before any write ----------------------------------------------------------------


def test_removing_the_old_key_before_apply_is_refused_and_adding_it_back_restores_the_rows(
    engine, configure
):
    plaintexts = ["one", "two", "three"]
    ids = _seed(engine, configure, "k1", plaintexts)
    before = _stored(engine)

    configure("k2")  # the old key was dropped instead of retired
    for value in before.values():
        with pytest.raises(crypto_mod.UnknownKeyError) as unknown:
            decrypt(value)
        assert unknown.value.key_id == "k1"
    code, report = _run(engine, "--check")
    assert code == EXIT_REFUSED and "3 value(s) name key id 'k1'" in report
    with pytest.raises(ReencryptError) as refused:
        reencrypt.apply(engine, out=io.StringIO())
    assert all(str(i) in str(refused.value) for i in ids)
    assert _stored(engine) == before  # nothing was modified

    configure("k2", "k1")
    _assert_plaintexts(engine, ids, plaintexts)
    assert _run(engine, "--check")[0] == EXIT_PENDING
    assert _run(engine, "--apply")[0] == EXIT_OK
    _assert_plaintexts(engine, ids, plaintexts)


def test_an_unknown_key_id_in_a_late_row_refuses_before_any_write(engine, configure):
    """1100 convertible rows, one under an unconfigured key: not even the first batch is written."""
    good_ids = _seed(engine, configure, "k1", [f"ok {n}" for n in range(1100)])
    secret = "patient has a very specific diagnosis"
    configure("k9")
    [bad_id] = _insert(engine, [encrypt(secret)])
    configure("k2", "k1")  # k9 is configured nowhere
    before = _stored(engine)

    with pytest.raises(ReencryptError) as excinfo:
        reencrypt.apply(engine, out=io.StringIO())

    message = str(excinfo.value)
    assert "1 value(s) name key id 'k9'" in message and str(bad_id) in message
    assert str(good_ids[0]) not in message
    assert secret not in message and before[bad_id] not in message
    assert _stored(engine) == before  # no row converted, though 1100 were convertible


def test_a_value_that_does_not_decrypt_is_refused_and_named(engine, configure):
    ids = _seed(engine, configure, "k1", ["a", "b"])
    configure("k2")
    [wrong_key] = _insert(engine, [encrypt("c")])
    with engine.begin() as conn:
        # a k1 envelope made by k2's key: the prefix selects k1's key, whose tag check fails
        conn.execute(
            text(
                "UPDATE clinical_entry SET description = replace(description, 'mh1:k2:', 'mh1:k1:')"
                " WHERE id = :i"
            ),
            {"i": wrong_key},
        )
    [raw_id, empty_id] = _insert(engine, ["not-an-envelope", ""])
    configure("k2", "k1")
    before = _stored(engine)

    code, report = _run(engine, "--check")
    assert code == EXIT_REFUSED and "3 value(s) do not decrypt" in report
    with pytest.raises(ReencryptError) as excinfo:
        reencrypt.apply(engine, out=io.StringIO())
    for bad in (wrong_key, raw_id, empty_id):
        assert str(bad) in str(excinfo.value)
    assert str(ids[0]) not in str(excinfo.value)
    assert _stored(engine) == before


# ----- failure handling -------------------------------------------------------------------------


def test_failure_mid_batch_rolls_that_batch_back_and_a_rerun_finishes(
    engine, configure, monkeypatch
):
    plaintexts = [f"v{n}" for n in range(8)]
    ids = _seed(engine, configure, "k1", plaintexts)
    configure("k2", "k1")
    real, calls = crypto_mod.encrypt, {"n": 0}

    def flaky(value: str) -> str:
        calls["n"] += 1
        if calls["n"] == 5:  # the second row of the second batch of three
            raise RuntimeError("simulated crash")
        return real(value)

    monkeypatch.setattr(crypto_mod, "encrypt", flaky)
    with pytest.raises(RuntimeError, match="simulated crash"):
        reencrypt.apply(engine, batch_size=3, out=io.StringIO())

    assert _kids(engine) == {"k1": 5, "k2": 3}  # batch 1 committed, batch 2 rolled back whole
    _assert_plaintexts(engine, ids, plaintexts)
    monkeypatch.setattr(crypto_mod, "encrypt", real)
    assert _run(engine, "--apply")[0] == EXIT_OK
    assert _kids(engine) == {"k2": 8}


def test_a_new_value_that_does_not_read_back_to_the_plaintext_stops_the_batch(
    engine, configure, monkeypatch
):
    ids = _seed(engine, configure, "k1", ["alpha", "beta"])
    configure("k2", "k1")
    real = crypto_mod.encrypt
    monkeypatch.setattr(crypto_mod, "encrypt", lambda v: real(v + "!"))  # writes the wrong text
    before = _stored(engine)

    with pytest.raises(ReencryptError, match="failed the read-back check; batch rolled back"):
        reencrypt.apply(engine, out=io.StringIO())

    assert _stored(engine) == before
    monkeypatch.setattr(crypto_mod, "encrypt", real)
    _assert_plaintexts(engine, ids, ["alpha", "beta"])


def test_a_value_the_database_stores_differently_stops_the_batch_before_commit(engine, configure):
    """The row read back from the database (not the Python value) is compared before commit."""
    ids = _seed(engine, configure, "k1", ["alpha", "beta", "gamma"])
    configure("k2", "k1")
    before = _stored(engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE FUNCTION mangle() RETURNS trigger AS $$ BEGIN "
                "NEW.description := substr(NEW.description, 1, length(NEW.description) - 1) "
                "|| 'A'; RETURN NEW; END $$ LANGUAGE plpgsql"
            )
        )
        conn.execute(
            text(
                "CREATE TRIGGER mangle BEFORE UPDATE ON clinical_entry "
                "FOR EACH ROW EXECUTE FUNCTION mangle()"
            )
        )
    try:
        with pytest.raises(ReencryptError, match="failed the read-back check in the database"):
            reencrypt.apply(engine, out=io.StringIO())
    finally:
        with engine.begin() as conn:
            conn.execute(text("DROP TRIGGER mangle ON clinical_entry"))
            conn.execute(text("DROP FUNCTION mangle()"))

    assert _stored(engine) == before
    _assert_plaintexts(engine, ids, ["alpha", "beta", "gamma"])


def test_the_batch_holds_a_lock_that_blocks_writers_but_not_readers(
    engine, configure, monkeypatch, pg_container
):
    _seed(engine, configure, "k1", [f"v{n}" for n in range(6)])
    configure("k2", "k1")
    gate, started = threading.Event(), threading.Event()
    real, calls = crypto_mod.encrypt, {"n": 0}

    def hold(value: str) -> str:
        calls["n"] += 1
        if calls["n"] == 2:  # inside the first batch, the lock is held
            started.set()
            gate.wait(30)
        return real(value)

    monkeypatch.setattr(crypto_mod, "encrypt", hold)
    errors: list[BaseException] = []

    def run() -> None:
        try:
            reencrypt.apply(engine, batch_size=3, out=io.StringIO())
        except BaseException as exc:  # noqa: BLE001 - reported by the assertion below
            errors.append(exc)

    worker = threading.Thread(target=run)
    worker.start()
    other = create_engine(pg_container.get_connection_url())
    try:
        assert started.wait(60), "the command did not reach its first batch"
        with other.connect() as conn:
            conn.execute(text("SET statement_timeout = '3s'"))
            assert len(conn.execute(text("SELECT description FROM clinical_entry")).all()) == 6
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
    assert _kids(engine) == {"k2": 6}


def test_a_writer_that_holds_the_table_makes_the_command_stop_without_a_change(
    engine, configure, monkeypatch
):
    _seed(engine, configure, "k1", ["a", "b"])
    configure("k2", "k1")
    before = _stored(engine)
    monkeypatch.setattr(reencrypt, "LOCK_TIMEOUT_MS", 300)
    with engine.connect() as writer:  # an open write transaction on the table
        writer.execute(text("UPDATE clinical_entry SET description = description"))
        with pytest.raises(OperationalError, match="lock timeout"):
            reencrypt.apply(engine, out=io.StringIO())
        writer.rollback()
    assert _stored(engine) == before


# ----- the guard and the command line -----------------------------------------------------------


def test_verify_key_ids_refuses_an_unconfigured_key_id_without_decrypting(
    engine, configure, monkeypatch
):
    ids = _seed(engine, configure, "k1", ["a", "b"])
    [raw_id] = _insert(engine, ["not-an-envelope"])
    configure("k2", "k1")
    out = io.StringIO()
    assert verify_key_ids(engine, out=out) == EXIT_OK  # k1 retired; the raw row is not its concern

    configure("k2")  # k1 removed while two values still name it
    monkeypatch.setattr(
        crypto_mod, "decrypt", lambda v: pytest.fail("the guard must not decrypt a value")
    )
    out = io.StringIO()
    assert verify_key_ids(engine, out=out) == EXIT_REFUSED
    text_out = out.getvalue()
    assert "2 value(s) name key id 'k1'" in text_out and all(str(i) in text_out for i in ids)
    assert str(raw_id) not in text_out and "Nothing was changed" in text_out


def test_command_line_exit_codes_and_no_value_in_any_output(engine, configure, capsys, monkeypatch):
    secret = "needle-in-the-clinical-text"
    _seed(engine, configure, "k1", [secret, "second"])
    configure("k2", "k1")
    stored = list(_stored(engine).values())
    keys = [_b64(KEYS[k]) for k in ("k1", "k2")]

    assert reencrypt.main(["--check"], engine=engine) == EXIT_PENDING
    assert reencrypt.main(["--apply", "--batch-size", "1"], engine=engine) == EXIT_OK
    assert reencrypt.main(["--check"], engine=engine) == EXIT_OK
    assert reencrypt.main(["--verify-key-ids"], engine=engine) == EXIT_OK
    configure("k3")  # neither k1 nor k2 configured any more, but the rows name k2
    assert reencrypt.main(["--check"], engine=engine) == EXIT_REFUSED
    assert reencrypt.main(["--apply"], engine=engine) == EXIT_REFUSED
    assert reencrypt.main(["--verify-key-ids"], engine=engine) == EXIT_REFUSED

    def boom(*_a, **_k):
        raise RuntimeError(f"driver says {secret} {keys[0]}")

    monkeypatch.setattr(reencrypt, "apply", boom)
    assert reencrypt.main(["--apply"], engine=engine) == EXIT_REFUSED
    captured = capsys.readouterr()
    everything = captured.out + captured.err
    assert "RuntimeError" in captured.err
    for forbidden in [secret, "second", *stored, *keys, *map(_b64, KEYS.values())]:
        assert forbidden not in everything
    stored_now = list(_stored(engine).values())
    for forbidden in stored_now:
        assert forbidden not in everything


def test_exactly_one_mode_is_required(engine):
    with pytest.raises(SystemExit) as excinfo:
        reencrypt.main([], engine=engine)
    assert excinfo.value.code == 2
    with pytest.raises(SystemExit):
        reencrypt.main(["--check", "--apply"], engine=engine)


def test_batch_size_must_be_positive(engine, configure):
    configure("k1")
    with pytest.raises(ReencryptError, match="at least 1"):
        reencrypt.apply(engine, batch_size=0, out=io.StringIO())


# ----- each batch reads its rows under the lock (QA round 1) ------------------------------------


@pytest.mark.parametrize("writer_kid", ["k1", "k2"])
def test_a_write_committed_while_apply_waits_for_the_lock_is_not_overwritten(
    engine, configure, pg_container, monkeypatch, writer_kid
):
    """The pre-scan sees the old value; the batch must read the committed one under the lock.

    An uncommitted writer holds a row of the first batch (batch size covers every row). ``apply``
    blocks on ``LOCK TABLE``; the writer then commits. If the batch had selected its rows before
    taking the lock, it would re-encrypt the stale value and overwrite the writer's text.
    """
    ids = _seed(engine, configure, "k1", [f"old {n}" for n in range(20)])
    target = ids[7]
    configure(writer_kid, *(["k1"] if writer_kid != "k1" else []))
    new_value = encrypt("NEW CLINICAL CONTENT")
    configure("k2", "k1")
    scanned: dict[str, dict[str, int]] = {}
    real_scan = reencrypt.scan

    def spy(conn, column, **kwargs):
        found = real_scan(conn, column, **kwargs)
        scanned.setdefault("counts", dict(found.counts))
        return found

    monkeypatch.setattr(reencrypt, "scan", spy)
    other = create_engine(pg_container.get_connection_url())
    errors: list[BaseException] = []

    def run() -> None:
        try:
            reencrypt.apply(engine, batch_size=50, out=io.StringIO())
        except BaseException as exc:  # noqa: BLE001 - reported by the assertion below
            errors.append(exc)

    worker = threading.Thread(target=run)
    try:
        with other.connect() as writer:
            writer.execute(
                text("UPDATE clinical_entry SET description = :d WHERE id = :i"),
                {"d": new_value, "i": target},
            )
            worker.start()
            deadline = time.time() + 30
            while "counts" not in scanned and time.time() < deadline:
                time.sleep(0.05)
            time.sleep(1)  # the command is now waiting for the table lock
            assert worker.is_alive()
            writer.commit()
        worker.join(30)
    finally:
        other.dispose()
    assert not errors, errors
    assert scanned["counts"] == {"k1": 20}  # the pre-scan saw the old value
    stored = _stored(engine)
    assert decrypt(stored[target]) == "NEW CLINICAL CONTENT"
    for n, row_id in enumerate(ids):
        if row_id != target:
            assert decrypt(stored[row_id]) == f"old {n}"
    assert set(_kids(engine)) == {"k2"}


def test_a_value_written_between_the_pre_scan_and_a_batch_is_converted_as_written(
    engine, configure, pg_container, monkeypatch
):
    ids = _seed(engine, configure, "k1", [f"old {n}" for n in range(10)])
    new_value = encrypt("written by an old process after the scan")  # still under k1
    configure("k2", "k1")
    other = create_engine(pg_container.get_connection_url())
    real, fired = reencrypt._convert_batch, {"n": 0}

    def wrapped(*args, **kwargs):
        if fired["n"] == 0:
            fired["n"] = 1
            with other.begin() as writer:
                writer.execute(
                    text("UPDATE clinical_entry SET description = :d WHERE id = :i"),
                    {"d": new_value, "i": ids[3]},
                )
        return real(*args, **kwargs)

    monkeypatch.setattr(reencrypt, "_convert_batch", wrapped)
    try:
        reencrypt.apply(engine, batch_size=4, out=io.StringIO())
    finally:
        other.dispose()
    assert decrypt(_stored(engine)[ids[3]]) == "written by an old process after the scan"
    assert _kids(engine) == {"k2": 10}


def test_batches_continue_after_the_last_converted_id_and_a_final_sweep_finds_late_rows(
    engine, configure, monkeypatch
):
    ids = _seed(engine, configure, "k1", [f"v{n}" for n in range(9)])
    ordered = sorted(ids)
    configure("k2", "k1")
    real, seen = reencrypt._convert_batch, []

    def spy(conn, column, current_id, size, after=None):
        seen.append(after)
        done = real(conn, column, current_id, size, after)
        if len(seen) == 1:  # a k1 value appears behind the cursor after the first batch
            conn.commit()
            with conn.engine.begin() as writer:
                writer.execute(
                    text("UPDATE clinical_entry SET description = :d WHERE id = :i"),
                    {"d": encrypt_k1, "i": ordered[0]},
                )
        return done

    configure("k1")
    encrypt_k1 = encrypt("late k1 value")
    configure("k2", "k1")
    monkeypatch.setattr(reencrypt, "_convert_batch", spy)
    real_batches, starts = reencrypt._batches, []

    def record(*args, **kwargs):
        starts.append(kwargs.get("start_after"))
        return real_batches(*args, **kwargs)

    monkeypatch.setattr(reencrypt, "_batches", record)
    reencrypt.apply(engine, batch_size=4, out=io.StringIO())

    assert ordered[3] in starts  # the query of the second batch starts after the first batch
    assert seen[0] is None and seen[1] == ordered[3]  # the second batch starts after the first
    assert seen[-1] is None  # and one sweep from the start closes the run
    assert _kids(engine) == {"k2": 9}
    assert decrypt(_stored(engine)[ordered[0]]) == "late k1 value"
