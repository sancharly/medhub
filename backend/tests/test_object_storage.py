"""CR-001 / TASK-157: ObjectStorageClient is built from the declared boto3 SDK.

Deliberately no patch, stub, importorskip or sys.modules entry for boto3: the real SDK must be
installed (declared under [project] dependencies) for this test to pass. boto3.client("s3", ...)
opens no connection, so no object-storage endpoint needs to be reachable.
"""

import io

import pytest
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.core.object_storage import ObjectChangedError, ObjectStorageClient


def test_object_storage_client_builds_real_s3_client() -> None:
    get_settings.cache_clear()
    try:
        client = ObjectStorageClient()
    finally:
        get_settings.cache_clear()

    assert client._bucket == "medhub"
    assert client._client.meta.endpoint_url == "http://localhost:9000"


def _client_with_stub():
    from botocore.stub import Stubber  # noqa: PLC0415

    get_settings.cache_clear()
    try:
        client = ObjectStorageClient()
    finally:
        get_settings.cache_clear()
    return client, Stubber(client._client)


def test_get_object_stream_returns_chunks_and_etag_without_reading_the_body() -> None:
    """SR-013 AC 6: the body is handed back as a stream; ``IfMatch`` is sent only when given."""
    from botocore.response import StreamingBody  # noqa: PLC0415

    data = b"x" * 150_000
    client, stub = _client_with_stub()
    stub.add_response(
        "get_object",
        {"Body": StreamingBody(io.BytesIO(data), len(data)), "ETag": '"abc"'},
        {"Bucket": "medhub", "Key": "k", "IfMatch": '"abc"'},
    )
    with stub:
        chunks, etag = client.get_object_stream("k", if_match='"abc"')
        parts = list(chunks)

    assert etag == '"abc"'
    assert [len(p) for p in parts] == [65536, 65536, 18928]


def test_get_object_stream_maps_precondition_failed_to_object_changed() -> None:
    """SR-013 AC 5 (D-10): a 412 from the store is ObjectChangedError, any other error passes."""
    client, stub = _client_with_stub()
    stub.add_client_error("get_object", "PreconditionFailed", http_status_code=412)
    stub.add_client_error("get_object", "NoSuchKey", http_status_code=404)
    with stub:
        with pytest.raises(ObjectChangedError):
            client.get_object_stream("k", if_match='"old"')
        with pytest.raises(ClientError):
            client.get_object_stream("k", if_match='"old"')
