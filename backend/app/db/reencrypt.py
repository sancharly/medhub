"""Field-encryption key rotation: ``python -m app.db.reencrypt`` (SR-022 AC 8, ADR-0018, TASK-195).

Runs as the database owner (``DATABASE_OWNER_URL``), from the ``db-migrate`` image. It covers every
``EncryptedString`` column of the models (found from ``Base.metadata``, so a future column is
covered without a change here).

``--check``
    Read only. Decrypts every value and prints the number of values per key id. Exit 0: every value
    is readable and names the current key. Exit 3: every value is readable, but some name a retired
    key (a rotation is pending). Exit 1: some value names a key id that is not configured, or does
    not decrypt (no envelope, malformed, edited, wrong key); the row ids are printed (first 100).
``--apply [--batch-size N]``
    Re-encrypts every value that does not name the current key id, under the current key.
    1. Refuses, before writing anything, if ``--check`` would exit 1 (counts and row ids printed).
    2. Converts in batches. Each batch is one transaction: ``LOCK TABLE ... SHARE ROW EXCLUSIVE``
       (the lock of migration 0010: writers wait, readers continue), select the next values not
       under the current key, decrypt, encrypt under the current key, decrypt the new value and
       compare it with the plaintext, update, read the rows back from the database and compare
       again, commit. Any mismatch or error rolls the whole batch back and stops.
    Each batch commits on its own, so an interrupted run leaves every row readable under the current
    or a retired key; running it again continues. A second run converts nothing. The lock is held
    for one batch only, and the application can stay up: it writes under the current key.
``--verify-key-ids``
    Read only, does not decrypt. Exit 1 if some value names a key id that is not configured. The
    ``db-migrate`` service runs it after the migrations, so a retired key cannot be removed while a
    stored value still needs it.

Output names counts, key ids, table and column names and row ids. It never prints a value, a
ciphertext or a key, and database errors are reduced to their class name for that reason.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from typing import Any

import sqlalchemy as sa
from sqlalchemy import Connection, Engine, MetaData

from app.db import crypto
from app.db.types import EncryptedString

BATCH_SIZE = 500
MAX_IDS_REPORTED = 100
LOCK_TIMEOUT_MS = 10_000  # wait this long for the table lock, then stop (a re-run is safe)
UNREADABLE = "unreadable"  # counter label for a value that is not an mh1 envelope

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_PENDING = 3


class ReencryptError(RuntimeError):
    """A refusal or a failed batch. The message holds counts, key ids and row ids, never a value."""


@dataclass(frozen=True)
class Column:
    table: str
    id_column: str
    name: str

    @property
    def label(self) -> str:
        return f"{self.table}.{self.name}"

    def sql_table(self) -> sa.TableClause:
        # A plain String column: the ORM type would encrypt and decrypt on its own.
        return sa.table(self.table, sa.column(self.id_column), sa.column(self.name, sa.String))


def discover(metadata: MetaData | None = None) -> list[Column]:
    """Every ``EncryptedString`` column of the models, with its single-column primary key."""
    if metadata is None:
        import app.db.models  # noqa: F401, PLC0415 - registers every model
        from app.db.models.base import Base  # noqa: PLC0415

        metadata = Base.metadata
    columns = []
    for table in metadata.sorted_tables:
        for column in table.columns:
            if isinstance(column.type, EncryptedString):
                pk = list(table.primary_key.columns)
                if len(pk) != 1:
                    raise ReencryptError(f"{table.name} needs a single-column primary key")
                columns.append(Column(table.name, pk[0].name, column.name))
    return columns


@dataclass
class Scan:
    """What one column holds: values per key id, and the rows that cannot be read."""

    counts: Counter[str] = field(default_factory=Counter)
    unknown_key: dict[str, list[Any]] = field(default_factory=dict)  # key id -> row ids
    unreadable: list[Any] = field(default_factory=list)  # row ids

    @property
    def ok(self) -> bool:
        return not self.unknown_key and not self.unreadable

    def pending(self, current_id: str) -> int:
        return sum(n for kid, n in self.counts.items() if kid != current_id)


def _batches(
    conn: Connection,
    column: Column,
    *,
    only_not_under: str | None,
    size: int = BATCH_SIZE,
    start_after: Any = None,
) -> Iterator[list[tuple[Any, str]]]:
    """Non-NULL values by primary key, in batches; optionally only those not under a key id."""
    table = column.sql_table()
    id_col, value_col = table.c[column.id_column], table.c[column.name]
    last = start_after
    while True:
        stmt = sa.select(id_col, value_col).where(value_col.is_not(None)).order_by(id_col)
        if only_not_under is not None:
            under = value_col.startswith(f"mh1:{only_not_under}:", autoescape=True)
            stmt = stmt.where(sa.not_(under))
        if last is not None:
            stmt = stmt.where(id_col > last)
        rows = [(row[0], row[1]) for row in conn.execute(stmt.limit(size))]
        if not rows:
            return
        yield rows
        last = rows[-1][0]


def _decrypt(value: str) -> str | None:
    try:
        return crypto.decrypt(value)
    except Exception:  # noqa: BLE001 - never keep the exception: it may describe the value
        return None


def scan(conn: Connection, column: Column, *, decrypt: bool = True) -> Scan:
    """Classify every value of ``column`` by the key id in its envelope.

    With ``decrypt`` a value is also decrypted, so a damaged or wrong-key value is reported.
    """
    ring = crypto.get_keyring()
    result = Scan()
    for batch in _batches(conn, column, only_not_under=None):
        for row_id, value in batch:
            try:
                key_id, _ = crypto.parse(value)
            except crypto.CiphertextFormatError:
                result.counts[UNREADABLE] += 1
                result.unreadable.append(row_id)
                continue
            result.counts[key_id] += 1
            if key_id not in ring.keys:
                result.unknown_key.setdefault(key_id, []).append(row_id)
            elif decrypt and _decrypt(value) is None:
                result.unreadable.append(row_id)
    return result


def _ids(ids: Sequence[Any]) -> str:
    shown = ", ".join(str(i) for i in sorted(ids, key=str)[:MAX_IDS_REPORTED])
    more = f" (first {MAX_IDS_REPORTED} of {len(ids)})" if len(ids) > MAX_IDS_REPORTED else ""
    return f"{more}: {shown}"


def problems(column: Column, found: Scan, *, unreadable: bool = True) -> list[str]:
    """One line per problem, with counts and row ids; empty when the column is fine."""
    lines = [
        f"{column.label}: {len(ids)} value(s) name key id '{kid}', which is not configured; "
        f"row ids{_ids(ids)}"
        for kid, ids in sorted(found.unknown_key.items())
    ]
    if unreadable and found.unreadable:
        lines.append(
            f"{column.label}: {len(found.unreadable)} value(s) do not decrypt (no mh1 envelope, "
            f"damaged, or the key does not match); row ids{_ids(found.unreadable)}"
        )
    return lines


def _format_counts(counts: Counter[str], current_id: str) -> str:
    if not counts:
        return "no values"
    parts = [
        f"{kid}={n}" + (" (current)" if kid == current_id else "")
        for kid, n in sorted(counts.items())
    ]
    return ", ".join(parts)


def _refuse(lines: list[str]) -> ReencryptError:
    return ReencryptError(
        "refused, nothing was changed:\n  - "
        + "\n  - ".join(lines)
        + "\nKeep (or put back) every key these values need in AT_REST_ENCRYPTION_KEY or "
        "AT_REST_ENCRYPTION_RETIRED_KEYS; see infra/DEPLOY.md, 'Field-encryption key rotation'."
    )


def check(engine: Engine, *, out: Any = None) -> int:
    """Print the per-key counts of every encrypted column; return the exit code."""
    out = out or sys.stdout
    ring = crypto.get_keyring()
    code = EXIT_OK
    for column in discover():
        with engine.connect() as conn:
            found = scan(conn, column)
        print(f"{column.label}: {_format_counts(found.counts, ring.current_id)}", file=out)
        for line in problems(column, found):
            print(f"  PROBLEM {line}", file=out)
        if not found.ok:
            code = EXIT_REFUSED
        elif found.pending(ring.current_id) and code == EXIT_OK:
            code = EXIT_PENDING
    if code == EXIT_PENDING:
        print("rotation pending: some values are under a retired key", file=out)
    return code


def verify_key_ids(engine: Engine, *, out: Any = None) -> int:
    """Refuse (exit 1) when a stored value names a key id that is not configured."""
    out = out or sys.stdout
    lines: list[str] = []
    summary: list[str] = []
    current_id = crypto.get_keyring().current_id
    for column in discover():
        with engine.connect() as conn:
            found = scan(conn, column, decrypt=False)
        summary.append(f"{column.label}: {_format_counts(found.counts, current_id)}")
        lines += problems(column, found, unreadable=False)
    if not lines:
        print("field-encryption key ids verified; " + "; ".join(summary), file=out)
    if lines:
        print("stored values need a key that is not configured:", file=out)
        for line in lines:
            print(f"  - {line}", file=out)
        print(
            "Put the key back in AT_REST_ENCRYPTION_RETIRED_KEYS (or restore a backup); see "
            "infra/DEPLOY.md, 'Field-encryption key rotation'. Nothing was changed.",
            file=out,
        )
        return EXIT_REFUSED
    return EXIT_OK


def _convert_batch(
    conn: Connection, column: Column, current_id: str, size: int, after: Any = None
) -> list[tuple[Any, str]]:
    """Convert the next batch inside the caller's transaction; return (row id, plaintext)."""
    table = column.sql_table()
    id_col, value_col = table.c[column.id_column], table.c[column.name]
    preparer = conn.dialect.identifier_preparer
    conn.execute(sa.text(f"SET LOCAL lock_timeout = {int(LOCK_TIMEOUT_MS)}"))
    conn.execute(sa.text(f"LOCK TABLE {preparer.quote(column.table)} IN SHARE ROW EXCLUSIVE MODE"))
    batch = next(
        _batches(conn, column, only_not_under=current_id, size=size, start_after=after), None
    )
    if not batch:
        return []
    converted: list[tuple[Any, str]] = []
    for row_id, value in batch:
        plaintext = _decrypt(value)
        if plaintext is None:
            raise ReencryptError(
                f"{column.label}: row {row_id} does not decrypt; batch rolled back"
            )
        new_value = crypto.encrypt(plaintext)
        if _decrypt(new_value) != plaintext:
            raise ReencryptError(
                f"{column.label}: row {row_id} failed the read-back check; batch rolled back"
            )
        conn.execute(sa.update(table).where(id_col == row_id).values({column.name: new_value}))
        converted.append((row_id, plaintext))
    # Read the rows back from the database, inside the transaction, before it commits.
    stored = {
        row[0]: row[1]
        for row in conn.execute(
            sa.select(id_col, value_col).where(id_col.in_([row_id for row_id, _ in converted]))
        )
    }
    for row_id, plaintext in converted:
        stored_value = stored.get(row_id)
        if (
            stored_value is None
            or not stored_value.startswith(f"mh1:{current_id}:")
            or _decrypt(stored_value) != plaintext
        ):
            raise ReencryptError(
                f"{column.label}: row {row_id} failed the read-back check in the database; "
                "batch rolled back"
            )
    return converted


def apply(engine: Engine, *, batch_size: int = BATCH_SIZE, out: Any = None) -> int:
    """Re-encrypt every value not under the current key id. Raises ``ReencryptError``."""
    out = out or sys.stdout
    if batch_size < 1:
        raise ReencryptError("--batch-size must be at least 1")
    ring = crypto.get_keyring()
    columns = discover()
    before: dict[str, Scan] = {}
    refusals: list[str] = []
    for column in columns:  # pass 1: read only; nothing is written if any value is unreadable
        with engine.connect() as conn:
            before[column.label] = scan(conn, column)
        refusals += problems(column, before[column.label])
    if refusals:
        raise _refuse(refusals)
    for column in columns:
        counts = _format_counts(before[column.label].counts, ring.current_id)
        print(f"{column.label} before: {counts}", file=out)
        total, batches, cursor = 0, 0, None
        while before[column.label].pending(ring.current_id):  # nothing pending: no lock, no write
            with engine.begin() as conn:  # one transaction, one commit, per batch
                done = _convert_batch(conn, column, ring.current_id, batch_size, cursor)
            if done:
                total, batches, cursor = total + len(done), batches + 1, done[-1][0]
            elif cursor is not None:
                cursor = None  # one sweep from the start: a row written behind the cursor
            else:
                break
        with engine.connect() as conn:
            after = scan(conn, column)
        print(f"{column.label} converted: {total} value(s) in {batches} batch(es)", file=out)
        print(f"{column.label} after: {_format_counts(after.counts, ring.current_id)}", file=out)
        if not after.ok or after.pending(ring.current_id):
            raise ReencryptError(f"{column.label}: values remain under another key after apply")
    return EXIT_OK


def _engine() -> Engine:
    url = (os.environ.get("DATABASE_OWNER_URL") or "").strip()
    if not url:
        sys.exit("DATABASE_OWNER_URL must be set: the command runs as the owner role")
    # hide_parameters: a failing statement must not print the values it carried
    return sa.create_engine(url, hide_parameters=True)


def main(argv: Sequence[str] | None = None, engine: Engine | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.db.reencrypt", description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="count values per key id; read only")
    mode.add_argument("--apply", action="store_true", help="re-encrypt to the current key")
    mode.add_argument(
        "--verify-key-ids", action="store_true", help="refuse if a stored key id is not configured"
    )
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args(argv)
    if engine is None:
        from app.core.secret_settings import enforce  # noqa: PLC0415

        enforce()  # the same rule as db-migrate: refuse placeholders before connecting
        engine = _engine()
    try:
        if args.check:
            return check(engine)
        if args.verify_key_ids:
            return verify_key_ids(engine)
        return apply(engine, batch_size=args.batch_size)
    except ReencryptError as exc:
        print(f"reencrypt {exc}", file=sys.stderr)
        return EXIT_REFUSED
    except Exception as exc:  # noqa: BLE001 - class name only: a database error can carry values
        print(
            f"reencrypt failed: {type(exc).__name__}; the failing batch was rolled back, "
            "run the command again (see the database log for the cause)",
            file=sys.stderr,
        )
        return EXIT_REFUSED
    finally:
        engine.dispose()


if __name__ == "__main__":
    sys.exit(main())
