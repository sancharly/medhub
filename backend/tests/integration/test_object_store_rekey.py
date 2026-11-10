"""The attachment copy and the start-up read-back against a real object store (TASK-196).

Skipped unless ``OBJECT_STORE_INTEGRATION=1`` (see test_object_store_sse.py for how the store is
started). One store holds one SSE key, so a copy between two keys needs two stores; that run is
the rehearsal in infra/DEPLOY.md. What this checks against the real server is everything else the
copy relies on: ``S3Store`` reads and writes with AES256, the SHA-256 compare passes for empty,
small and large objects, a re-run copies nothing, and the initialiser's read-back of a stored
object passes on a store whose key matches its data.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import sys
import uuid
from collections.abc import Iterator
from pathlib import Path

import boto3
import pytest

from app.core.config import get_settings
from app.core.object_store_init import initialise

pytestmark = [
    pytest.mark.object_store,
    pytest.mark.skipif(
        os.environ.get("OBJECT_STORE_INTEGRATION") != "1",
        reason="needs a real object store: set OBJECT_STORE_INTEGRATION=1",
    ),
]

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "migrate_object_store.py"
spec = importlib.util.spec_from_file_location("migrate_object_store_it", SCRIPT)
assert spec is not None and spec.loader is not None
mos = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mos
spec.loader.exec_module(mos)

# The root conftest overwrites OBJECT_STORE_* with fake values for every test; keep the real ones.
_REAL_STORE_ENV = {k: v for k, v in os.environ.items() if k.startswith("OBJECT_STORE_")}


@pytest.fixture(autouse=True)
def _real_store_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in _REAL_STORE_ENV.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()


@pytest.fixture
def buckets() -> Iterator[tuple[str, str]]:
    settings = get_settings()
    client = _boto(settings)
    names = (f"rekey-src-{uuid.uuid4().hex[:10]}", f"rekey-dst-{uuid.uuid4().hex[:10]}")
    for name in names:
        client.create_bucket(Bucket=name)
    yield names
    for name in names:
        for page in client.get_paginator("list_objects_v2").paginate(Bucket=name):
            for item in page.get("Contents", []):
                client.delete_object(Bucket=name, Key=item["Key"])
        client.delete_bucket(Bucket=name)


def _boto(settings):  # type: ignore[no-untyped-def]
    return boto3.client(
        "s3",
        endpoint_url=settings.object_store_endpoint,
        aws_access_key_id=settings.object_store_access_key.get_secret_value(),
        aws_secret_access_key=settings.object_store_secret_key.get_secret_value(),
        region_name="us-east-1",
    )


def _store(settings, bucket: str):  # type: ignore[no-untyped-def]
    return mos.S3Store(
        settings.object_store_endpoint,
        settings.object_store_access_key.get_secret_value(),
        settings.object_store_secret_key.get_secret_value(),
        bucket,
    )


def test_copy_verifies_every_object_and_a_rerun_copies_nothing(buckets) -> None:
    src_bucket, dst_bucket = buckets
    settings = get_settings()
    source, target = _store(settings, src_bucket), _store(settings, dst_bucket)
    payloads = {
        "attachments/p1/a/empty.txt": b"",
        "attachments/p1/b/small.pdf": os.urandom(1500),
        "attachments/p2/c/large.bin": os.urandom(6 * 1024 * 1024),
    }
    rows = []
    for key, data in payloads.items():
        source.put(key, data, "application/octet-stream")
        rows.append(mos.Row(key, hashlib.sha256(data).hexdigest(), "application/octet-stream"))

    first = mos.migrate(rows, source, target)
    assert first.ok and len(first.copied) == 3, vars(first)
    assert {k: target.get(k) for k in payloads} == payloads
    head = _boto(settings).head_object(Bucket=dst_bucket, Key="attachments/p2/c/large.bin")
    assert head["ServerSideEncryption"] == "AES256"

    second = mos.migrate(rows, source, target)
    assert second.ok and second.copied == [] and len(second.already_present) == 3


def test_initialiser_reads_back_a_stored_object_on_a_store_whose_key_matches(buckets) -> None:
    src_bucket, _ = buckets
    settings = get_settings()
    _store(settings, src_bucket).put("attachments/p1/a/file.bin", os.urandom(300), "x/y")
    initialise(_boto(settings), src_bucket)  # raises InitError if the stored object is unreadable
