"""Conditional read checked against a real object store (TASK-217, SOUP-036 behaviour 14).

SR-013 AC 5, D-10: the second pass of a download reads with ``If-Match: <ETag>``, so an object
replaced between the passes is refused by the store (412) and never served. Skipped unless
``OBJECT_STORE_INTEGRATION=1`` (the real store of the ``object-store-integration`` job), like
``test_object_store_sse.py``.
"""

import io
import os
import uuid
from collections.abc import Iterator

import pytest
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.core.object_storage import ObjectChangedError, ObjectStorageClient

pytestmark = [
    pytest.mark.object_store,
    pytest.mark.skipif(
        os.environ.get("OBJECT_STORE_INTEGRATION") != "1",
        reason="needs a real object store: set OBJECT_STORE_INTEGRATION=1",
    ),
]

_REAL_STORE_ENV = {k: v for k, v in os.environ.items() if k.startswith("OBJECT_STORE_")}


@pytest.fixture(autouse=True)
def _real_store_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in _REAL_STORE_ENV.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()


@pytest.fixture
def key() -> Iterator[str]:
    name = f"integration/{uuid.uuid4()}"
    yield name
    ObjectStorageClient().delete_object(name)


def _put(key: str, data: bytes) -> None:
    ObjectStorageClient().put_object(key, io.BytesIO(data), len(data), "application/octet-stream")


def test_stream_with_the_current_etag_returns_the_bytes(key):
    data = os.urandom(200_000)
    _put(key, data)
    client = ObjectStorageClient()

    _, etag = client.get_object_stream(key)
    chunks, _ = client.get_object_stream(key, if_match=etag)

    assert b"".join(chunks) == data


def test_replaced_object_is_refused_with_object_changed(key):
    """SR-013 AC 5: If-Match with the earlier ETag after an overwrite answers 412, no content."""
    _put(key, os.urandom(200_000))
    client = ObjectStorageClient()
    _, old_etag = client.get_object_stream(key)

    _put(key, os.urandom(200_000))

    with pytest.raises(ObjectChangedError):
        client.get_object_stream(key, if_match=old_etag)


def test_etag_without_quotes_behaves_the_same(key):
    data = os.urandom(1000)
    _put(key, data)
    client = ObjectStorageClient()
    _, etag = client.get_object_stream(key)

    chunks, _ = client.get_object_stream(key, if_match=etag.strip('"'))
    assert b"".join(chunks) == data
    _put(key, os.urandom(1000))
    with pytest.raises(ObjectChangedError):
        client.get_object_stream(key, if_match=etag.strip('"'))


def test_missing_object_is_not_reported_as_changed():
    with pytest.raises(ClientError) as excinfo:
        ObjectStorageClient().get_object_stream(f"integration/{uuid.uuid4()}", if_match='"abc"')
    assert excinfo.value.response["Error"]["Code"] == "NoSuchKey"
