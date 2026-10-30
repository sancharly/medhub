"""Object-store bucket initialiser (SR-040 AC 4, SR-022 AC 4, ADD-025 U-OBJ-Init, PRB-039).

Run once at bring-up as ``python -m app.core.object_store_init`` from the backend image, after
the store is healthy. Plain S3 calls through boto3, so it is independent of the server product:
create the bucket if missing, set SSE-S3 (AES256) as its default encryption, read it back, and
check that the bucket carries no policy. Exit 0 only when every step holds; otherwise exit 1 with
one line on stderr naming the failed step. Safe to re-run. Key values are never printed.

It reads the four ``OBJECT_STORE_*`` variables directly instead of ``get_settings()``: the
initialiser container receives only these four, and ``Settings`` also requires database, SMTP
and session settings that it must not hold.
"""

from __future__ import annotations

import os
import sys
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
)

ENCRYPTION = "AES256"
_MISSING_BUCKET = {"404", "NoSuchBucket", "NotFound"}


class InitError(Exception):
    """A failed initialisation step; the message is the one line printed."""


def unreachable_message(exc: Exception) -> str:
    return f"object store unreachable: {exc}"


def _code(exc: ClientError) -> str:
    return str(exc.response.get("Error", {}).get("Code", ""))


def _failed(step: str, exc: ClientError) -> InitError:
    return InitError(f"{step} failed: {_code(exc)}")


def initialise(client: Any, bucket: str) -> None:
    """Make ``bucket`` exist, encrypted by default and policy-free; raise InitError otherwise."""
    try:
        try:
            client.head_bucket(Bucket=bucket)
        except ClientError as exc:
            if _code(exc) not in _MISSING_BUCKET:
                raise _failed("head_bucket", exc) from exc
            try:
                client.create_bucket(Bucket=bucket)
            except ClientError as create_exc:
                raise _failed("create_bucket", create_exc) from create_exc

        try:
            client.put_bucket_encryption(
                Bucket=bucket,
                ServerSideEncryptionConfiguration={
                    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": ENCRYPTION}}]
                },
            )
        except ClientError as exc:
            raise _failed("put_bucket_encryption", exc) from exc

        try:
            config = client.get_bucket_encryption(Bucket=bucket)
        except ClientError as exc:
            raise _failed("get_bucket_encryption", exc) from exc
        rules = config.get("ServerSideEncryptionConfiguration", {}).get("Rules", [])
        algorithms = [
            rule.get("ApplyServerSideEncryptionByDefault", {}).get("SSEAlgorithm") for rule in rules
        ]
        if algorithms != [ENCRYPTION]:
            raise InitError(
                f"get_bucket_encryption returned {algorithms or 'no rule'}, expected [{ENCRYPTION}]"
            )

        try:
            client.get_bucket_policy(Bucket=bucket)
        except ClientError as exc:
            if _code(exc) != "NoSuchBucketPolicy":
                raise _failed("get_bucket_policy", exc) from exc
        else:
            raise InitError("bucket has a policy; it must stay private")
    except EndpointConnectionError as exc:
        raise InitError(unreachable_message(exc)) from exc
    except NoCredentialsError as exc:
        raise InitError("no object-store credentials") from exc


def main() -> int:
    names = (
        "OBJECT_STORE_ENDPOINT",
        "OBJECT_STORE_ACCESS_KEY",
        "OBJECT_STORE_SECRET_KEY",
        "OBJECT_STORE_BUCKET",
    )
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        absent = ", ".join(missing)
        print(f"object-store init failed: environment lacks {absent}", file=sys.stderr)
        return 1
    client = boto3.client(
        "s3",
        endpoint_url=os.environ["OBJECT_STORE_ENDPOINT"],
        aws_access_key_id=os.environ["OBJECT_STORE_ACCESS_KEY"],
        aws_secret_access_key=os.environ["OBJECT_STORE_SECRET_KEY"],
        region_name="us-east-1",
        config=Config(
            connect_timeout=5, read_timeout=15, retries={"max_attempts": 2, "mode": "standard"}
        ),
    )
    try:
        initialise(client, os.environ["OBJECT_STORE_BUCKET"])
    except InitError as exc:
        print(f"object-store init failed: {exc}", file=sys.stderr)
        return 1
    print(f"object-store init ok: bucket {os.environ['OBJECT_STORE_BUCKET']} private, {ENCRYPTION}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
