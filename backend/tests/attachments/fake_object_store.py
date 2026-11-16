"""A fake object store for the download tests (TASK-217).

Mirrors the part of ``ObjectStorageClient`` the download uses: ``get_object`` (bytes) and
``get_object_stream`` (chunks, ETag, ``If-Match`` honoured with ``ObjectChangedError``). It records
every call, and can swap the content after a given read to model an object replaced between the
two passes of a download, or serve different bytes on the second read.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator

from app.core.object_storage import ObjectChangedError

CHUNK = 65536


class FakeObjectStore:
    def __init__(
        self,
        data: bytes = b"",
        *,
        replace_after_read: bytes | None = None,
        second_read_bytes: bytes | None = None,
        error: Exception | None = None,
    ) -> None:
        self.data = data
        self._replace_after_read = replace_after_read
        self._second_read_bytes = second_read_bytes
        self._error = error
        self.calls: list[tuple[str, str | None]] = []  # (method, if_match)
        self.stream_reads = 0

    @property
    def etag(self) -> str:
        return '"' + hashlib.md5(self.data, usedforsecurity=False).hexdigest() + '"'

    def get_object(self, key: str) -> bytes:
        self.calls.append(("get_object", None))
        if self._error is not None:
            raise self._error
        return self.data

    def get_object_stream(
        self, key: str, if_match: str | None = None
    ) -> tuple[Iterator[bytes], str]:
        self.calls.append(("get_object_stream", if_match))
        if self._error is not None:
            raise self._error
        if if_match is not None and if_match != self.etag:
            raise ObjectChangedError(key)
        self.stream_reads += 1
        etag = self.etag
        content = self.data
        if self.stream_reads == 2 and self._second_read_bytes is not None:
            content = self._second_read_bytes
        if self.stream_reads == 1 and self._replace_after_read is not None:
            replacement = self._replace_after_read
            self.data = replacement
        return (content[i : i + CHUNK] for i in range(0, len(content), CHUNK)), etag
