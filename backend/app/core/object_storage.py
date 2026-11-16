"""ObjectStorageClient — MinIO / S3-compatible object storage (TASK-045).

boto3 is a required runtime dependency (declared in pyproject.toml, locked in uv.lock). The
import stays lazy so that importing this module needs no SDK; the client raises ImportError at
instantiation time if boto3 is missing, rather than at module import time.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import BinaryIO

from app.core.config import get_settings

_CHUNK_SIZE = 65536  # 64 KiB


class ObjectChangedError(Exception):
    """The object no longer has the ETag the caller named (HTTP 412 ``PreconditionFailed``)."""


class ObjectStorageClient:
    def __init__(self) -> None:
        try:
            import boto3  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "boto3 is required for object storage. Install it with: pip install boto3"
            ) from exc

        settings = get_settings()
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.object_store_endpoint,
            aws_access_key_id=settings.object_store_access_key.get_secret_value(),
            aws_secret_access_key=settings.object_store_secret_key.get_secret_value(),
        )
        self._bucket = settings.object_store_bucket

    def put_object(self, key: str, fileobj: BinaryIO, size: int, content_type: str) -> None:
        """Upload ``size`` bytes of ``fileobj`` with SSE-AES256 server-side encryption.

        One ``PutObject`` with the file as body, never ``upload_fileobj`` (SOUP-019, SOUP-036 issue
        #8908): the object is read from the file, not held in memory (SR-013 AC 6).
        """
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=fileobj,
            ContentLength=size,
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )

    def get_object(self, key: str) -> bytes:
        """Download bytes from object storage."""
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()  # type: ignore[no-any-return]

    def get_object_stream(
        self, key: str, if_match: str | None = None
    ) -> tuple[Iterator[bytes], str]:
        """Open an object and return (64 KiB chunks, ETag) without reading it into memory.

        The response is opened before this returns, so a failure (and, with ``if_match``, a 412
        mapped to ``ObjectChangedError``) is raised before the caller starts a response
        (SR-013 AC 5 and AC 6, ADR-0021; SOUP-036 relied-on behaviour 14).
        """
        options = {"IfMatch": if_match} if if_match is not None else {}
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key, **options)
        except Exception as exc:
            error = getattr(exc, "response", {}).get("Error", {})
            if error.get("Code") == "PreconditionFailed":
                raise ObjectChangedError(key) from exc
            raise
        body = response["Body"]

        def _chunks() -> Iterator[bytes]:
            try:
                yield from body.iter_chunks(_CHUNK_SIZE)
            finally:
                body.close()

        return _chunks(), response["ETag"]

    def delete_object(self, key: str) -> None:
        """Delete an object from storage. Best-effort — ignores errors."""
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except Exception:
            pass
