"""TASK-175: object-store bucket initialiser (SR-040 AC 4, SR-022 AC 4, TS-014 TC-014.4)."""

import io
import os
import subprocess
import sys

import boto3
import pytest
from botocore.config import Config
from botocore.exceptions import ConnectionClosedError, EndpointConnectionError, ReadTimeoutError
from botocore.stub import Stubber

from app.core.object_store_init import InitError, initialise

BUCKET = "medhub"
ENC_CONFIG = {"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}


def _client():
    return boto3.client(
        "s3",
        endpoint_url="http://store:9000",
        aws_access_key_id="k",
        aws_secret_access_key="s",
        region_name="us-east-1",
        config=Config(retries={"max_attempts": 0}),
    )


def _enc_params():
    return {"Bucket": BUCKET, "ServerSideEncryptionConfiguration": ENC_CONFIG}


def _tail(stub: Stubber, encryption=ENC_CONFIG, policy_error="NoSuchBucketPolicy") -> None:
    stub.add_response("put_bucket_encryption", {}, _enc_params())
    stub.add_response(
        "get_bucket_encryption",
        {"ServerSideEncryptionConfiguration": encryption},
        {"Bucket": BUCKET},
    )
    if policy_error:
        stub.add_client_error(
            "get_bucket_policy", service_error_code=policy_error, http_status_code=404
        )
        if policy_error == "NoSuchBucketPolicy":  # the last step reads back what the bucket holds
            stub.add_response("list_objects_v2", {"KeyCount": 0}, {"Bucket": BUCKET})
    else:
        stub.add_response("get_bucket_policy", {"Policy": "{}"}, {"Bucket": BUCKET})


def test_fresh_bucket_is_created_encrypted_and_private() -> None:
    c = _client()
    with Stubber(c) as stub:
        stub.add_client_error("head_bucket", service_error_code="404", http_status_code=404)
        stub.add_response("create_bucket", {}, {"Bucket": BUCKET})
        _tail(stub)
        initialise(c, BUCKET)
        stub.assert_no_pending_responses()


def test_existing_bucket_is_not_recreated() -> None:
    c = _client()
    with Stubber(c) as stub:
        stub.add_response("head_bucket", {}, {"Bucket": BUCKET})
        _tail(stub)
        initialise(c, BUCKET)
        stub.assert_no_pending_responses()


def test_second_run_is_idempotent() -> None:
    c = _client()
    with Stubber(c) as stub:
        for _ in range(2):
            stub.add_response("head_bucket", {}, {"Bucket": BUCKET})
            _tail(stub)
        initialise(c, BUCKET)
        initialise(c, BUCKET)
        stub.assert_no_pending_responses()


def test_head_bucket_forbidden_fails_without_creating() -> None:
    c = _client()
    with Stubber(c) as stub:
        stub.add_client_error("head_bucket", service_error_code="403", http_status_code=403)
        with pytest.raises(InitError, match="head_bucket"):
            initialise(c, BUCKET)
        stub.assert_no_pending_responses()


def test_create_bucket_error_fails() -> None:
    c = _client()
    with Stubber(c) as stub:
        stub.add_client_error("head_bucket", service_error_code="404", http_status_code=404)
        stub.add_client_error("create_bucket", service_error_code="AccessDenied")
        with pytest.raises(InitError, match="create_bucket"):
            initialise(c, BUCKET)


def test_put_bucket_encryption_error_fails() -> None:
    c = _client()
    with Stubber(c) as stub:
        stub.add_response("head_bucket", {}, {"Bucket": BUCKET})
        stub.add_client_error(
            "put_bucket_encryption", service_error_code="NotImplemented", http_status_code=501
        )
        with pytest.raises(InitError, match="put_bucket_encryption"):
            initialise(c, BUCKET)


@pytest.mark.parametrize(
    "encryption",
    [
        {"Rules": []},
        {"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms"}}]},
    ],
)
def test_unexpected_encryption_readback_fails(encryption) -> None:
    c = _client()
    with Stubber(c) as stub:
        stub.add_response("head_bucket", {}, {"Bucket": BUCKET})
        _tail(stub, encryption=encryption)
        with pytest.raises(InitError, match="get_bucket_encryption returned"):
            initialise(c, BUCKET)


def test_policy_present_fails() -> None:
    c = _client()
    with Stubber(c) as stub:
        stub.add_response("head_bucket", {}, {"Bucket": BUCKET})
        _tail(stub, policy_error=None)
        with pytest.raises(InitError, match="policy"):
            initialise(c, BUCKET)


def test_other_policy_error_fails() -> None:
    c = _client()
    with Stubber(c) as stub:
        stub.add_response("head_bucket", {}, {"Bucket": BUCKET})
        _tail(stub, policy_error="AccessDenied")
        with pytest.raises(InitError, match="get_bucket_policy"):
            initialise(c, BUCKET)


def test_endpoint_unreachable_fails() -> None:
    class Unreachable:
        def head_bucket(self, **_: object) -> None:
            raise EndpointConnectionError(endpoint_url="http://store:9000")

    with pytest.raises(InitError, match="unreachable"):
        initialise(Unreachable(), BUCKET)


@pytest.mark.parametrize(
    "error",
    [
        ConnectionClosedError(endpoint_url="http://store:9000"),
        ReadTimeoutError(endpoint_url="http://store:9000"),
    ],
)
def test_other_transport_error_is_one_line_not_a_traceback(error) -> None:
    """TASK-175 QA carry-over: any botocore transport error becomes an InitError."""

    class Broken:
        def head_bucket(self, **_: object) -> None:
            raise error

    with pytest.raises(InitError, match=f"object store error: {type(error).__name__}"):
        initialise(Broken(), BUCKET)


def _run_main(extra_env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("OBJECT_STORE_")}
    env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-m", "app.core.object_store_init"],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )


def test_main_exits_1_when_store_unreachable() -> None:
    result = _run_main(
        {
            "OBJECT_STORE_ENDPOINT": "http://127.0.0.1:1",
            "OBJECT_STORE_ACCESS_KEY": "a1b2c3d4e5f6a1b2c3d4e5f6",
            "OBJECT_STORE_SECRET_KEY": "Zx9Qw3Lm7Rt2Vb5Nk8Hy4Jd6Fg1Sa0Pc",
            "OBJECT_STORE_BUCKET": BUCKET,
        }
    )
    assert result.returncode == 1
    assert "object-store init failed" in result.stderr
    assert "Zx9Qw3Lm7Rt2Vb5Nk8Hy4Jd6Fg1Sa0Pc" not in result.stderr + result.stdout


def test_main_exits_1_when_settings_missing() -> None:
    result = _run_main({})
    assert result.returncode == 1
    assert "OBJECT_STORE_ENDPOINT" in result.stderr


# TASK-196, SR-041 AC 5: a store started with the wrong SSE key for its volume is caught here
_OBJECT = {"Contents": [{"Key": "attachments/p/a/file.pdf", "Size": 20}], "KeyCount": 1}


def _up_to_the_probe(stub: Stubber) -> None:
    stub.add_response("head_bucket", {}, {"Bucket": BUCKET})
    stub.add_response("put_bucket_encryption", {}, _enc_params())
    stub.add_response(
        "get_bucket_encryption",
        {"ServerSideEncryptionConfiguration": ENC_CONFIG},
        {"Bucket": BUCKET},
    )
    stub.add_client_error(
        "get_bucket_policy", service_error_code="NoSuchBucketPolicy", http_status_code=404
    )
    stub.add_response("list_objects_v2", _OBJECT, {"Bucket": BUCKET})


def test_a_readable_stored_object_passes() -> None:
    c = _client()
    with Stubber(c) as stub:
        _up_to_the_probe(stub)
        stub.add_response(
            "get_object",
            {"Body": io.BytesIO(b"%")},
            {"Bucket": BUCKET, "Key": "attachments/p/a/file.pdf", "Range": "bytes=0-0"},
        )
        initialise(c, BUCKET)
        stub.assert_no_pending_responses()


def test_an_unreadable_stored_object_is_refused_naming_the_setting_not_the_key() -> None:
    c = _client()
    with Stubber(c) as stub:
        _up_to_the_probe(stub)
        stub.add_client_error(
            "get_object", service_error_code="InternalError", http_status_code=500
        )
        with pytest.raises(InitError) as exc:
            initialise(c, BUCKET)
    assert "OBJECT_STORE_SSE_KEY" in str(exc.value) and "InternalError" in str(exc.value)
    assert "attachments/" not in str(exc.value)


def test_a_zero_byte_object_is_read_whole_because_a_wrong_key_fails_it_too() -> None:
    """Rehearsal finding: under a wrong key an empty object answers 500; a range on it is 416."""
    c = _client()
    listing = {"Contents": [{"Key": "attachments/p/a/empty", "Size": 0}], "KeyCount": 1}
    with Stubber(c) as stub:
        stub.add_response("head_bucket", {}, {"Bucket": BUCKET})
        stub.add_response("put_bucket_encryption", {}, _enc_params())
        stub.add_response(
            "get_bucket_encryption",
            {"ServerSideEncryptionConfiguration": ENC_CONFIG},
            {"Bucket": BUCKET},
        )
        stub.add_client_error(
            "get_bucket_policy", service_error_code="NoSuchBucketPolicy", http_status_code=404
        )
        stub.add_response("list_objects_v2", listing, {"Bucket": BUCKET})
        stub.add_client_error(
            "get_object", service_error_code="InternalError", http_status_code=500
        )
        with pytest.raises(InitError, match="OBJECT_STORE_SSE_KEY"):
            initialise(c, BUCKET)


def test_the_smallest_object_of_the_page_is_the_one_read() -> None:
    c = _client()
    listing = {
        "Contents": [
            {"Key": "big", "Size": 5_000_000},
            {"Key": "small", "Size": 10},
            {"Key": "mid", "Size": 4000},
        ],
        "KeyCount": 3,
    }
    with Stubber(c) as stub:
        stub.add_response("head_bucket", {}, {"Bucket": BUCKET})
        stub.add_response("put_bucket_encryption", {}, _enc_params())
        stub.add_response(
            "get_bucket_encryption",
            {"ServerSideEncryptionConfiguration": ENC_CONFIG},
            {"Bucket": BUCKET},
        )
        stub.add_client_error(
            "get_bucket_policy", service_error_code="NoSuchBucketPolicy", http_status_code=404
        )
        stub.add_response("list_objects_v2", listing, {"Bucket": BUCKET})
        stub.add_response(
            "get_object",
            {"Body": io.BytesIO(b"x")},
            {"Bucket": BUCKET, "Key": "small", "Range": "bytes=0-0"},
        )
        initialise(c, BUCKET)
        stub.assert_no_pending_responses()


def _stub_to_listing(stub: Stubber, listing: dict) -> None:
    stub.add_response("head_bucket", {}, {"Bucket": BUCKET})
    stub.add_response("put_bucket_encryption", {}, _enc_params())
    stub.add_response(
        "get_bucket_encryption",
        {"ServerSideEncryptionConfiguration": ENC_CONFIG},
        {"Bucket": BUCKET},
    )
    stub.add_client_error(
        "get_bucket_policy", service_error_code="NoSuchBucketPolicy", http_status_code=404
    )
    stub.add_response("list_objects_v2", listing, {"Bucket": BUCKET})


def test_a_readable_zero_byte_object_is_read_without_a_range() -> None:
    """A range on a zero-byte object answers InvalidRange even with the right key."""
    c = _client()
    listing = {"Contents": [{"Key": "attachments/p/a/empty", "Size": 0}], "KeyCount": 1}
    with Stubber(c) as stub:
        _stub_to_listing(stub, listing)
        stub.add_response(
            "get_object",
            {"Body": io.BytesIO(b"")},
            {"Bucket": BUCKET, "Key": "attachments/p/a/empty"},
        )
        initialise(c, BUCKET)
        stub.assert_no_pending_responses()


@pytest.mark.parametrize("code, status", [("AccessDenied", 403), ("SlowDown", 503)])
def test_other_probe_errors_are_a_failed_get_object_not_a_wrong_key(code: str, status: int) -> None:
    c = _client()
    with Stubber(c) as stub:
        _stub_to_listing(stub, _OBJECT)
        stub.add_client_error("get_object", service_error_code=code, http_status_code=status)
        with pytest.raises(InitError) as exc:
            initialise(c, BUCKET)
    assert str(exc.value) == f"get_object failed: {code}"
    assert "OBJECT_STORE_SSE_KEY" not in str(exc.value)


def test_an_object_gone_since_the_listing_is_looked_for_again_once() -> None:
    c = _client()
    with Stubber(c) as stub:
        _stub_to_listing(stub, _OBJECT)
        stub.add_client_error("get_object", service_error_code="NoSuchKey", http_status_code=404)
        stub.add_response("list_objects_v2", {"KeyCount": 0}, {"Bucket": BUCKET})
        initialise(c, BUCKET)
        stub.assert_no_pending_responses()


def test_an_object_gone_twice_is_a_failed_get_object() -> None:
    c = _client()
    with Stubber(c) as stub:
        _stub_to_listing(stub, _OBJECT)
        stub.add_client_error("get_object", service_error_code="NoSuchKey", http_status_code=404)
        stub.add_response("list_objects_v2", _OBJECT, {"Bucket": BUCKET})
        stub.add_client_error("get_object", service_error_code="NoSuchKey", http_status_code=404)
        with pytest.raises(InitError, match="get_object failed: NoSuchKey"):
            initialise(c, BUCKET)
