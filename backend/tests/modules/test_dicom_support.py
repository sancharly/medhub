"""Host unit tests of the shared DICOM helper (CR-008 D-B, TASK-234; TC-019.6, TC-019.7).

The helper is tested on streams. The objects are built by the DICOM viewer module's fixtures,
loaded by path because the module's own ``tests`` package shadows ``backend/tests``.
"""

from __future__ import annotations

import importlib.util
import io
import zlib
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from pydicom.uid import DeflatedExplicitVRLittleEndian, ExplicitVRLittleEndian

from app.modules import dicom_support
from app.modules.dicom_support import (
    DeflateStreamError,
    InflatedSizeExceeded,
    check_inflated_size,
    read_transfer_syntax,
)

_spec = importlib.util.spec_from_file_location(
    "dicom_viewer_fixtures",
    Path(__file__).parents[2] / "modules" / "dicom_viewer" / "tests" / "fixtures.py",
)
assert _spec is not None and _spec.loader is not None
fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fixtures)

LIMIT = 1024 * 1024
UID_BYTES = b"1.2.840.10008.1.2.1\x00"
# (0002,0010) that pydicom reads but cannot convert: an unknown VR, and a UV of the wrong length.
_UNCONVERTIBLE_SYNTAX_ELEMENTS = (
    fixtures.with_file_meta_element(fixtures.element(2, 0x10, b"ZZ", UID_BYTES)),
    fixtures.with_file_meta_element(fixtures.element(2, 0x10, b"UV", b"\x01\x02\x03\x04")),
)


def _inflated_size(data: bytes) -> int:
    return len(zlib.decompressobj(-zlib.MAX_WBITS).decompress(data[fixtures.file_meta_end(data) :]))


@contextmanager
def _counting_decompressor() -> Iterator[list[int]]:
    """The output sizes of each ``decompress`` call of the helper."""
    sizes: list[int] = []
    real = zlib.decompressobj

    class Counting:
        def __init__(self, *args: Any) -> None:
            self._inner = real(*args)

        def __getattr__(self, name: str) -> Any:
            return getattr(self._inner, name)

        def decompress(self, data: bytes, max_length: int = 0) -> bytes:
            out = self._inner.decompress(data, max_length)
            sizes.append(len(out))
            return out

    with patch.object(dicom_support.zlib, "decompressobj", Counting):
        yield sizes


def test_reads_the_declared_transfer_syntax_and_restores_the_offset() -> None:
    data, _ = fixtures.build_dicom(DeflatedExplicitVRLittleEndian)
    fp = io.BytesIO(data)
    fp.seek(77)

    assert read_transfer_syntax(fp) == DeflatedExplicitVRLittleEndian
    assert fp.tell() == 0


@pytest.mark.parametrize("uid", ["1.2.840.10008.1.2.4.50", "1.2.3.4"])
def test_reports_an_unsupported_syntax_as_declared(uid: str) -> None:
    """The helper reports; the allow-list is the caller's."""
    assert read_transfer_syntax(io.BytesIO(fixtures.build_compressed(uid))) == uid


def test_missing_syntax_preamble_or_file_meta_is_none() -> None:
    no_syntax, _ = fixtures.build_dicom(None)
    for data in (
        no_syntax,
        fixtures.build_dicom()[0][132:],
        b"",
        b"\x00" * 200,
        *_UNCONVERTIBLE_SYNTAX_ELEMENTS,
    ):
        fp = io.BytesIO(data)
        assert read_transfer_syntax(fp) is None
        assert fp.tell() == 0


def test_valid_deflated_object_within_the_bound_passes() -> None:
    data, _ = fixtures.build_dicom(DeflatedExplicitVRLittleEndian, rows=64, columns=64)
    fp = io.BytesIO(data)

    check_inflated_size(fp, 10 * LIMIT)

    assert fp.tell() == 0


def test_the_bound_is_exact() -> None:
    data, _ = fixtures.build_dicom(DeflatedExplicitVRLittleEndian, rows=64, columns=64)
    size = _inflated_size(data)

    check_inflated_size(io.BytesIO(data), size)
    with pytest.raises(InflatedSizeExceeded):
        check_inflated_size(io.BytesIO(data), size - 1)


@pytest.mark.parametrize("pad_byte", [False, True], ids=["no_pad_byte", "pad_byte"])
def test_valid_object_inflating_over_one_chunk_returns(pad_byte: bool) -> None:
    """A stream of odd length is followed by a pad byte; the check must still end (TC-019.7)."""
    data, expected = fixtures.build_large_deflated(pad_byte=pad_byte)
    assert expected.nbytes > dicom_support.CHUNK_SIZE
    fp = io.BytesIO(data)

    fixtures.call_with_timeout(lambda: check_inflated_size(fp, 1 << 30))

    assert fp.tell() == 0
    size = _inflated_size(data)
    fixtures.call_with_timeout(lambda: check_inflated_size(io.BytesIO(data), size))
    with pytest.raises(InflatedSizeExceeded):
        fixtures.call_with_timeout(lambda: check_inflated_size(io.BytesIO(data), size - 1))


def test_bomb_stops_within_the_bound_plus_one_chunk() -> None:
    bomb = fixtures.build_deflate_bomb(64 * LIMIT, incompressible_prefix=LIMIT // 4)
    assert len(bomb) > 2 * dicom_support.CHUNK_SIZE
    reads: list[int] = []

    class SpyStream(io.BytesIO):
        def read(self, size: int | None = -1) -> bytes:
            data = super().read(size)
            reads.append(len(data))
            return data

    fp = SpyStream(bomb)

    with _counting_decompressor() as sizes, pytest.raises(InflatedSizeExceeded):
        fixtures.call_with_timeout(lambda: check_inflated_size(fp, LIMIT))

    assert LIMIT < sum(sizes) <= LIMIT + dicom_support.CHUNK_SIZE
    assert max(sizes) <= dicom_support.CHUNK_SIZE
    assert reads and max(reads) <= dicom_support.CHUNK_SIZE  # unbounded fp.read() is caught here
    assert fp.tell() == 0


def test_corrupt_stream_raises_deflate_stream_error() -> None:
    fp = io.BytesIO(fixtures.build_corrupt_deflate())

    with pytest.raises(DeflateStreamError):
        check_inflated_size(fp, LIMIT)
    assert fp.tell() == 0


def test_truncated_stream_raises_deflate_stream_error() -> None:
    data, _ = fixtures.build_dicom(DeflatedExplicitVRLittleEndian, rows=64, columns=64)

    with pytest.raises(DeflateStreamError):
        check_inflated_size(io.BytesIO(data[:-10]), 10 * LIMIT)


def test_unreadable_file_meta_raises_deflate_stream_error() -> None:
    with pytest.raises(DeflateStreamError):
        check_inflated_size(io.BytesIO(b"\x00" * 200), LIMIT)


def test_explicit_vr_little_endian_has_no_special_handling_in_read() -> None:
    data, _ = fixtures.build_dicom(ExplicitVRLittleEndian)
    assert read_transfer_syntax(io.BytesIO(data)) == ExplicitVRLittleEndian
