#!/usr/bin/env python
"""Migrate attachment objects from the legacy MinIO to the new object store (TASK-178).

CR-002 AC-11, SR-022, SR-013. For each ``attachment`` row: read the object from the source (the
legacy MinIO decrypts it), compare its SHA-256 with ``checksum``, write it to the target with
``ServerSideEncryption="AES256"``, read it back and compare again. Source objects with no row
(orphans) are listed and never copied. The source is only read. Safe to re-run: an object already
on the target with the recorded checksum is left alone.

Environment (values are never printed):
  DATABASE_URL                                  database holding the attachment rows
  SOURCE_ENDPOINT / _ACCESS_KEY / _SECRET_KEY / _BUCKET   the legacy store
  OBJECT_STORE_ENDPOINT / _ACCESS_KEY / _SECRET_KEY / _BUCKET   the new store

Exit: 0 every row copied or already present; 1 any object missing or mismatched, or no rows at
all while the source holds objects (wrong database); 2 bad setup. Output names rows by attachment
id and orphans by a short hash, never by storage key (it holds the patient id and file name).
"""

from __future__ import annotations

import hashlib
import io
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

# Ensure backend/ is on sys.path when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

_MISSING_CODES = {"404", "NoSuchKey", "NotFound"}


@dataclass(frozen=True)
class Row:
    storage_key: str
    checksum: str
    content_type: str
    attachment_id: str = ""


class Store(Protocol):
    def get(self, key: str) -> bytes | None: ...
    def put(self, key: str, data: bytes, content_type: str) -> None: ...
    def keys(self) -> list[str]: ...


@dataclass
class Report:
    copied: list[str] = field(default_factory=list)
    already_present: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    mismatched: list[str] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)
    rows: int = 0
    # Printable names: the attachment id for a row, a short hash for an orphan. A storage key holds
    # the patient id and the file name (possible PHI), so keys are never printed.
    labels: dict[str, str] = field(default_factory=dict)

    @property
    def wrong_database(self) -> bool:
        """No rows but objects in the source: almost certainly the wrong database."""
        return self.rows == 0 and bool(self.orphans)

    @property
    def ok(self) -> bool:
        return not self.missing and not self.mismatched and not self.wrong_database


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()[:12]


def migrate(rows: list[Row], source: Store, target: Store) -> Report:
    report = Report(rows=len(rows))
    for row in rows:
        report.labels[row.storage_key] = row.attachment_id or _hash(row.storage_key)
        existing = target.get(row.storage_key)
        if existing is not None and _sha256(existing) == row.checksum:
            report.already_present.append(row.storage_key)
            continue
        data = source.get(row.storage_key)
        if data is None:
            report.missing.append(row.storage_key)
            continue
        if _sha256(data) != row.checksum:
            report.mismatched.append(row.storage_key)
            continue
        target.put(row.storage_key, data, row.content_type)
        written = target.get(row.storage_key)
        if written is None or _sha256(written) != row.checksum:
            report.mismatched.append(row.storage_key)
            continue
        report.copied.append(row.storage_key)
    known = {row.storage_key for row in rows}
    report.orphans = [key for key in source.keys() if key not in known]
    for key in report.orphans:
        report.labels[key] = _hash(key)
    return report


def exit_code(report: Report) -> int:
    return 0 if report.ok else 1


def print_report(report: Report) -> None:
    print(f"copied: {len(report.copied)}")
    print(f"already-present-and-matching: {len(report.already_present)}")
    print(f"missing-in-source: {len(report.missing)}")
    print(f"checksum-mismatch: {len(report.mismatched)}")
    print(f"orphans-in-source: {len(report.orphans)}")
    for label, keys in (
        ("MISSING", report.missing),
        ("MISMATCH", report.mismatched),
        ("ORPHAN", report.orphans),
    ):
        for key in keys:
            print(f"{label} {report.labels.get(key, _hash(key))}")
    if report.wrong_database:
        print(
            "error: no attachment rows but the source holds objects;"
            " is DATABASE_URL the live database?"
        )


class S3Store:
    """The few S3 calls the migration needs, over boto3."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str) -> None:
        import boto3

        self._client: Any = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self._bucket = bucket

    def get(self, key: str) -> bytes | None:
        from botocore.exceptions import ClientError

        try:
            body = self._client.get_object(Bucket=self._bucket, Key=key)["Body"].read()
        except ClientError as exc:
            if str(exc.response.get("Error", {}).get("Code", "")) in _MISSING_CODES:
                return None
            raise
        return bytes(body)

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=io.BytesIO(data),
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )

    def keys(self) -> list[str]:
        found: list[str] = []
        for page in self._client.get_paginator("list_objects_v2").paginate(Bucket=self._bucket):
            found.extend(item["Key"] for item in page.get("Contents", []))
        return found


def load_rows(database_url: str) -> list[Row]:
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    from app.db.models.attachment import Attachment

    engine = create_engine(database_url)
    with Session(engine) as session:
        result = session.execute(
            select(
                Attachment.storage_key,
                Attachment.checksum,
                Attachment.content_type,
                Attachment.id,
            )
        )
        return [Row(key, checksum, ctype, str(ident)) for key, checksum, ctype, ident in result]


def main(argv: list[str] | None = None) -> int:
    names = (
        "DATABASE_URL",
        "SOURCE_ENDPOINT",
        "SOURCE_ACCESS_KEY",
        "SOURCE_SECRET_KEY",
        "SOURCE_BUCKET",
        "OBJECT_STORE_ENDPOINT",
        "OBJECT_STORE_ACCESS_KEY",
        "OBJECT_STORE_SECRET_KEY",
        "OBJECT_STORE_BUCKET",
    )
    env = {name: os.environ.get(name, "") for name in names}
    unset = [name for name, value in env.items() if not value]
    if unset:
        print(f"error: set {', '.join(unset)}", file=sys.stderr)
        return 2
    source = S3Store(
        env["SOURCE_ENDPOINT"],
        env["SOURCE_ACCESS_KEY"],
        env["SOURCE_SECRET_KEY"],
        env["SOURCE_BUCKET"],
    )
    target = S3Store(
        env["OBJECT_STORE_ENDPOINT"],
        env["OBJECT_STORE_ACCESS_KEY"],
        env["OBJECT_STORE_SECRET_KEY"],
        env["OBJECT_STORE_BUCKET"],
    )
    report = migrate(load_rows(env["DATABASE_URL"]), source, target)
    print_report(report)
    return exit_code(report)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
