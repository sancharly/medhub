"""ObjectStorageClient — MinIO / S3-compatible object storage (TASK-045).

boto3 is an optional dependency. The client raises ImportError at instantiation time
if boto3 is not installed, rather than at module import time.
"""

from __future__ import annotations

import io

from app.core.config import get_settings


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

    def put_object(self, key: str, data: bytes, content_type: str) -> None:
        """Upload bytes to object storage with SSE-AES256 server-side encryption."""
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=io.BytesIO(data),
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )

    def get_object(self, key: str) -> bytes:
        """Download bytes from object storage."""
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()  # type: ignore[no-any-return]

    def delete_object(self, key: str) -> None:
        """Delete an object from storage. Best-effort — ignores errors."""
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except Exception:
            pass
