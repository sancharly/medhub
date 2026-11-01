"""Convert clinical_entry.description to the identified envelope (SR-022 AC 6/7, ADR-0018).

Before this revision the column held ``base64url(nonce || ciphertext)`` under the single
``AT_REST_ENCRYPTION_KEY``. Since TASK-193 the application reads and writes
``mh1:<kid>:<payload>`` only, so existing values must be re-encrypted under the current key id.
This is the only ``EncryptedString`` column (``clinical_entry.description``).

upgrade
    1. Locks the table against writers (SHARE ROW EXCLUSIVE; readers continue).
    2. Validation pass, read only: every value that does not start with ``mh1:`` must decrypt
       with ``decrypt_legacy`` under the current key. If any does not, nothing is written and the
       migration stops with the count and the row ids. Values and ciphertext are never reported.
    3. Conversion pass: each such value is re-encrypted with ``encrypt``, read back with
       ``decrypt`` and compared before the row is updated. Batches of 500 by primary key, so
       memory is bounded. NULL is left alone. Values that start with ``mh1:`` are never touched.
    The migration does not use the ORM type, so it does not depend on the application's read
    path (which refuses unprefixed values). Alembic runs the revision in one transaction, so an
    error in step 3 rolls back every row as well; a re-run finds nothing left to convert.
    Retired keys are not tried: the earlier format had a single key, the current one.

downgrade
    Re-encrypts ``mh1:`` values that name the current key back to the unprefixed format with the
    current key, so a rollback of the release can read them. If any value names another key id
    (or does not decrypt) it stops with the count and row ids and changes nothing: a retired key
    cannot be written back into a format that has no key identifier.

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-01
"""

from __future__ import annotations

import base64
import logging
import os
import uuid
from collections.abc import Callable, Iterator

import sqlalchemy as sa
from alembic import op
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.db import crypto

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

log = logging.getLogger("alembic.runtime.migration")  # the logger alembic prints at INFO

BATCH_SIZE = 500
MAX_IDS_REPORTED = 100
_PREFIX = "mh1:"

_clinical_entry = sa.table(
    "clinical_entry",
    sa.column("id", sa.Uuid),
    sa.column("description", sa.String),
)


class FieldMigrationError(RuntimeError):
    """A value cannot be converted. Carries row ids only, never a value."""


def _batches(bind: sa.Connection, *, enveloped: bool) -> Iterator[list[tuple[uuid.UUID, str]]]:
    """Rows with a non-NULL description that do (or do not) start with ``mh1:``, by id."""
    is_envelope = _clinical_entry.c.description.startswith(_PREFIX, autoescape=True)
    last: uuid.UUID | None = None
    while True:
        stmt = (
            sa.select(_clinical_entry.c.id, _clinical_entry.c.description)
            .where(_clinical_entry.c.description.is_not(None))
            .where(is_envelope if enveloped else sa.not_(is_envelope))
            .order_by(_clinical_entry.c.id)
            .limit(BATCH_SIZE)
        )
        if last is not None:
            stmt = stmt.where(_clinical_entry.c.id > last)
        rows = [(row.id, row.description) for row in bind.execute(stmt)]
        if not rows:
            return
        yield rows
        last = rows[-1][0]


def _refuse(direction: str, reason: str, ids: list[uuid.UUID]) -> FieldMigrationError:
    shown = ", ".join(str(i) for i in ids[:MAX_IDS_REPORTED])
    more = f" (first {MAX_IDS_REPORTED} of {len(ids)})" if len(ids) > MAX_IDS_REPORTED else ""
    return FieldMigrationError(
        f"migration 0010 {direction} refused: {len(ids)} clinical_entry.description value(s) "
        f"{reason}; row ids{more}: {shown}. Nothing was changed."
    )


def _legacy_decrypt(value: str, key: bytes) -> str | None:
    try:
        return crypto.decrypt_legacy(value, key)
    except Exception:  # noqa: BLE001 - never keep the exception: it may describe the value
        return None


def _envelope_decrypt(value: str) -> str | None:
    try:
        return crypto.decrypt(value)
    except Exception:  # noqa: BLE001 - never keep the exception: it may describe the value
        return None


def _legacy_encrypt(value: str, key: bytes) -> str:
    nonce = os.urandom(12)
    return base64.urlsafe_b64encode(
        nonce + AESGCM(key).encrypt(nonce, value.encode(), None)
    ).decode()


def _update(bind: sa.Connection, row_id: uuid.UUID, description: str) -> None:
    bind.execute(
        sa.update(_clinical_entry)
        .where(_clinical_entry.c.id == row_id)
        .values(description=description)
    )


def _lock(bind: sa.Connection) -> None:
    bind.execute(sa.text("LOCK TABLE clinical_entry IN SHARE ROW EXCLUSIVE MODE"))


def _run(
    direction: str,
    *,
    enveloped: bool,
    reason: str,
    decode: Callable[[str], str | None],
    encode: Callable[[str], str],
    read_back: Callable[[str], str | None],
) -> None:
    """``decode`` reads the stored form, ``encode`` writes the new one, ``read_back`` checks it."""
    bind = op.get_bind()
    _lock(bind)
    # Pass 1: read only. Any value that cannot be decoded stops the migration before a write.
    failed = [
        row_id
        for batch in _batches(bind, enveloped=enveloped)
        for row_id, value in batch
        if decode(value) is None
    ]
    if failed:
        raise _refuse(direction, reason, failed)
    # Pass 2: convert, verifying each value by reading the new form back.
    converted = 0
    for batch in _batches(bind, enveloped=enveloped):
        for row_id, value in batch:
            plaintext = decode(value)
            new_value = encode(plaintext) if plaintext is not None else None
            if new_value is None or read_back(new_value) != plaintext:
                raise _refuse(direction, "failed the read-back check", [row_id])
            _update(bind, row_id, new_value)
            converted += 1
    log.info(
        "migration 0010 %s: %d clinical_entry.description value(s) converted", direction, converted
    )


def _has_work(bind: sa.Connection, *, enveloped: bool) -> bool:
    return next(_batches(bind, enveloped=enveloped), None) is not None


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_work(bind, enveloped=False):
        return  # also needs no key settings on an empty or already converted table
    ring = crypto.get_keyring()
    key = ring.keys[ring.current_id]
    _run(
        "upgrade",
        enveloped=False,
        reason="do not decrypt with the current key (AT_REST_ENCRYPTION_KEY)",
        decode=lambda v: _legacy_decrypt(v, key),
        encode=crypto.encrypt,
        read_back=_envelope_decrypt,
    )


def downgrade() -> None:
    bind = op.get_bind()
    if not _has_work(bind, enveloped=True):
        return
    ring = crypto.get_keyring()
    key = ring.keys[ring.current_id]

    def decode(value: str) -> str | None:
        try:
            key_id, _ = crypto.parse(value)
            if key_id != ring.current_id:
                return None  # a retired key has no place in the unprefixed format
            return crypto.decrypt(value)
        except Exception:  # noqa: BLE001
            return None

    _run(
        "downgrade",
        enveloped=True,
        reason="do not name the current key id or do not decrypt",
        decode=decode,
        encode=lambda plaintext: _legacy_encrypt(plaintext, key),
        read_back=lambda v: _legacy_decrypt(v, key),
    )
