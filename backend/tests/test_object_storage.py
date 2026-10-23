"""CR-001 / TASK-157: ObjectStorageClient is built from the declared boto3 SDK.

Deliberately no patch, stub, importorskip or sys.modules entry for boto3: the real SDK must be
installed (declared under [project] dependencies) for this test to pass. boto3.client("s3", ...)
opens no connection, so no object-storage endpoint needs to be reachable.
"""

from app.core.config import get_settings
from app.core.object_storage import ObjectStorageClient


def test_object_storage_client_builds_real_s3_client() -> None:
    get_settings.cache_clear()
    try:
        client = ObjectStorageClient()
    finally:
        get_settings.cache_clear()

    assert client._bucket == "medhub"
    assert client._client.meta.endpoint_url == "http://localhost:9000"
