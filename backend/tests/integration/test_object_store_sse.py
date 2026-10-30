"""Server-side encryption checked against a real object store (TASK-179, PRB-036, TC-008.8).

Skipped unless ``OBJECT_STORE_INTEGRATION=1``: it needs the real store started by the CI job
``object-store-integration`` (or by hand, see TASK-179). The job's steps are for CI only: they
overwrite ``infra/.env``; run them by hand only after backing that file up. It reads the
endpoint and credentials from the same ``OBJECT_STORE_*`` variables as the application and
uses them without printing them.
"""

import os
import uuid
from collections.abc import Iterator

import boto3
import pytest
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.core.object_storage import ObjectStorageClient

pytestmark = [
    pytest.mark.object_store,
    pytest.mark.skipif(
        os.environ.get("OBJECT_STORE_INTEGRATION") != "1",
        reason="needs a real object store: set OBJECT_STORE_INTEGRATION=1",
    ),
]


# The root conftest overwrites OBJECT_STORE_* with fake values for every test; keep the real ones.
_REAL_STORE_ENV = {k: v for k, v in os.environ.items() if k.startswith("OBJECT_STORE_")}


@pytest.fixture(autouse=True)
def _real_store_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in _REAL_STORE_ENV.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()


@pytest.fixture
def raw_client():
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.object_store_endpoint,
        aws_access_key_id=settings.object_store_access_key.get_secret_value(),
        aws_secret_access_key=settings.object_store_secret_key.get_secret_value(),
    )


@pytest.fixture
def bucket() -> str:
    return get_settings().object_store_bucket


@pytest.fixture
def key(raw_client, bucket) -> Iterator[str]:
    name = f"integration/{uuid.uuid4()}"
    yield name
    raw_client.delete_object(Bucket=bucket, Key=name)


def test_put_object_stores_aes256_and_returns_the_original_bytes(raw_client, bucket, key):
    data = os.urandom(2048)
    ObjectStorageClient().put_object(key, data, "application/octet-stream")

    head = raw_client.head_object(Bucket=bucket, Key=key)
    assert head["ServerSideEncryption"] == "AES256"
    assert ObjectStorageClient().get_object(key) == data


def test_bucket_default_encryption_is_aes256(raw_client, bucket):
    rules = raw_client.get_bucket_encryption(Bucket=bucket)["ServerSideEncryptionConfiguration"][
        "Rules"
    ]
    assert [r["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"] for r in rules] == ["AES256"]


def test_upload_without_an_encryption_request_is_stored_aes256(raw_client, bucket, key):
    raw_client.put_object(Bucket=bucket, Key=key, Body=b"plain upload")

    head = raw_client.head_object(Bucket=bucket, Key=key)
    assert head["ServerSideEncryption"] == "AES256"


def test_put_object_requests_encryption_on_a_bucket_without_a_default(raw_client, monkeypatch):
    """The bucket default masks a missing request, so use a bucket that has none."""
    bucket = f"sse-nodefault-{uuid.uuid4().hex[:12]}"
    raw_client.create_bucket(Bucket=bucket)
    key = "integration/no-default"
    try:
        with pytest.raises(ClientError) as raised:
            raw_client.get_bucket_encryption(Bucket=bucket)
        assert (
            raised.value.response["Error"]["Code"]
            == "ServerSideEncryptionConfigurationNotFoundError"
        )

        monkeypatch.setenv("OBJECT_STORE_BUCKET", bucket)
        get_settings.cache_clear()
        ObjectStorageClient().put_object(key, b"x" * 100, "application/octet-stream")

        assert raw_client.head_object(Bucket=bucket, Key=key)["ServerSideEncryption"] == "AES256"
    finally:
        raw_client.delete_object(Bucket=bucket, Key=key)
        raw_client.delete_bucket(Bucket=bucket)
