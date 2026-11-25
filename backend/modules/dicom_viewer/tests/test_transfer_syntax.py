"""TASK-234: the transfer syntax is checked from the file meta information, and a Deflated
object's inflation is bounded, before any pixel decode (SR-017 AC 6 and AC 10; TC-019.6, TC-019.7).

Real objects built with pydicom and NumPy (``fixtures.py``); ``pydicom.dcmread`` and
``Dataset.pixel_array`` are spied on to show that nothing is parsed or decoded on a refusal.
"""

from __future__ import annotations

import struct
import zlib
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from unittest.mock import MagicMock, PropertyMock, patch

import pydicom
import pytest
from dicom_viewer.dicom import (
    SUPPORTED_FRAME_TRANSFER_SYNTAXES,
    _check_transfer_syntax,
    stream_dicom,
)
from pydicom.dataset import Dataset
from pydicom.uid import (
    DeflatedExplicitVRLittleEndian,
    ExplicitVRBigEndian,
    ExplicitVRLittleEndian,
    ImplicitVRLittleEndian,
    RLELossless,
)

from app.core.config import get_settings
from app.modules import dicom_support
from tests.fixtures import (
    build_compressed,
    build_corrupt_deflate,
    build_deflate_bomb,
    build_dicom,
    build_large_deflated,
    call_with_timeout,
    element,
    with_file_meta_element,
)
from tests.test_size_bounds import (
    FakeObjectStore,
    _assert_problem,
    _attachment,
    _client,
    _get,
)

LOW_BOUND = 1024 * 1024  # 1 MiB keeps the bomb tests small and fast


@pytest.fixture
def spies() -> Iterator[tuple[MagicMock, PropertyMock]]:
    """Spies on the full read and the decode; both must stay uncalled on a refusal."""
    with (
        patch.object(pydicom, "dcmread", side_effect=pydicom.dcmread) as dcmread,
        patch.object(Dataset, "pixel_array", PropertyMock()) as pixel_array,
    ):
        yield dcmread, pixel_array


@pytest.fixture
def low_bound(monkeypatch: pytest.MonkeyPatch) -> int:
    """``dicom_max_decoded_bytes`` set to 1 MiB, so a bomb test stays small and fast."""
    monkeypatch.setenv("DICOM_MAX_DECODED_BYTES", str(LOW_BOUND))
    get_settings.cache_clear()
    return LOW_BOUND


def _request(data: bytes):
    attachment = _attachment(data)
    return _get(_client(attachment, FakeObjectStore(data)), attachment)


@pytest.mark.parametrize(
    "uid",
    [
        "1.2.840.10008.1.2.4.50",  # JPEG Baseline
        "1.2.840.10008.1.2.4.90",  # JPEG 2000 Lossless
        "1.2.840.10008.1.2.4.201",  # HTJ2K
        "1.2.3.4",  # a private UID
    ],
)
def test_unsupported_transfer_syntax_refused_before_decode(uid: str, spies) -> None:
    """TC-019.6 (SR-017 AC 10): refused from the file meta information, naming the UID."""
    dcmread, pixel_array = spies
    resp = _request(build_compressed(uid))

    _assert_problem(resp, "dicom_transfer_syntax_unsupported")
    assert uid in resp.json()["errors"][0]["message"]
    assert "application/dicom" not in resp.headers["content-type"]
    dcmread.assert_not_called()


def test_missing_transfer_syntax_refused(spies) -> None:
    """TC-019.6 (SR-017 AC 10): no (0002,0010), and no preamble at all, are refused, not guessed."""
    dcmread, pixel_array = spies
    no_syntax, _ = build_dicom(None)
    no_preamble = build_dicom()[0][132:]
    # (0002,0010) that pydicom reads but cannot convert: an unknown VR, and a UV of the wrong length
    unknown_vr = with_file_meta_element(element(2, 0x10, b"ZZ", b"1.2.840.10008.1.2.1\x00"))
    wrong_length = with_file_meta_element(element(2, 0x10, b"UV", b"\x01\x02\x03\x04"))

    for data in (no_syntax, no_preamble, b"", unknown_vr, wrong_length):
        resp = _request(data)
        _assert_problem(resp, "dicom_transfer_syntax_unsupported")
        assert "declares no transfer syntax" in resp.json()["errors"][0]["message"]
    dcmread.assert_not_called()
    pixel_array.assert_not_called()


@pytest.mark.parametrize(
    "uid",
    [
        ImplicitVRLittleEndian,
        ExplicitVRLittleEndian,
        DeflatedExplicitVRLittleEndian,
        ExplicitVRBigEndian,
        RLELossless,
    ],
)
def test_supported_syntaxes_pass_the_check(uid: str) -> None:
    """TC-019.6: the five syntaxes of CR-008 D-3 (a) pass; the check returns the UID."""
    assert uid in SUPPORTED_FRAME_TRANSFER_SYNTAXES
    data = build_compressed(uid) if uid == RLELossless else build_dicom(uid)[0]
    assert _check_transfer_syntax(data) == uid
    assert len(SUPPORTED_FRAME_TRANSFER_SYNTAXES) == 5


def test_invalid_transfer_syntax_uid_is_not_echoed(spies) -> None:
    """TC-019.6: the declared value is untrusted: it is named only when it is a UID."""
    dcmread, pixel_array = spies
    huge = with_file_meta_element(
        struct.pack("<HH2sHI", 2, 0x10, b"OB", 0, 4 * 1024 * 1024) + b"1" * (4 * 1024 * 1024)
    )
    non_printable = with_file_meta_element(element(2, 0x10, b"UI", b"1.2.\x01\x02<b>\x1b[0m"))
    too_long = with_file_meta_element(element(2, 0x10, b"UI", b"1." * 32 + b"1"))

    for data, leaked in ((huge, "1111"), (non_printable, "<b>"), (too_long, "1.1.1.1")):
        resp = _request(data)
        _assert_problem(resp, "dicom_transfer_syntax_unsupported")
        body = resp.json()
        assert "invalid" in body["errors"][0]["message"]
        assert leaked not in resp.text
        assert len(resp.content) < 2048
    dcmread.assert_not_called()
    pixel_array.assert_not_called()


@pytest.mark.parametrize("pad_byte", [False, True], ids=["no_pad_byte", "pad_byte"])
def test_valid_deflated_object_over_one_chunk_returns_its_frame(pad_byte: bool) -> None:
    """TC-019.7 (RISK-007): a valid Deflated object inflating over one 64 KiB chunk, with and
    without the pad byte after the deflate stream, decodes; the frame path must not hang."""
    data, expected = build_large_deflated(pad_byte=pad_byte)
    assert expected.nbytes > dicom_support.CHUNK_SIZE

    # ``stream_dicom`` is what the router calls; a thread running it can be interrupted on a hang,
    # which the HTTP client's worker thread cannot.
    frame = call_with_timeout(lambda: stream_dicom(data, 0))

    assert frame == expected.tobytes()


def test_file_meta_read_does_not_parse_the_data_set() -> None:
    """TC-019.6: pins the reliance on pydicom's private ``_read_file_meta_info`` (SOUP-015 1.3).

    It must exist, read group 0002 only, and not inflate a Deflated data set. A pydicom upgrade that
    changes any of this fails here.
    """
    import pydicom.filereader as filereader

    assert callable(getattr(filereader, "_read_file_meta_info", None))
    data, _ = build_dicom(DeflatedExplicitVRLittleEndian)
    real_read_dataset = filereader.read_dataset
    with (
        patch.object(zlib, "decompress") as decompress,
        patch.object(zlib, "decompressobj") as decompressobj,
        patch.object(filereader, "read_dataset", side_effect=real_read_dataset) as read_dataset,
        patch.object(pydicom, "dcmread") as dcmread,
    ):
        uid = _check_transfer_syntax(data)

    assert uid == DeflatedExplicitVRLittleEndian
    decompress.assert_not_called()
    decompressobj.assert_not_called()
    dcmread.assert_not_called()
    # one read_dataset call, for group 0002 only (it stops at the first other group)
    assert read_dataset.call_count == 1
    assert read_dataset.call_args.kwargs["stop_when"] is not None


def test_deflate_bomb_refused_without_full_inflation(spies, low_bound: int) -> None:
    """TC-019.7 (SR-017 AC 6): a bomb above the bound is refused; the inflated count stops within
    one chunk of the bound."""
    dcmread, pixel_array = spies
    bomb = build_deflate_bomb(64 * low_bound)
    assert len(bomb) < 1024 * 1024

    with _counting_decompressor() as tally:
        resp = _request(bomb)

    _assert_problem(resp, "dicom_decoded_size_exceeded")
    assert low_bound < tally.total <= low_bound + dicom_support.CHUNK_SIZE
    dcmread.assert_not_called()
    pixel_array.assert_not_called()


def test_corrupt_deflate_stream_is_decode_failed(spies) -> None:
    """TC-019.7 (SR-017 AC 6): a corrupt deflate stream is a decode failure and returns no image."""
    dcmread, pixel_array = spies
    resp = _request(build_corrupt_deflate())

    _assert_problem(resp, "dicom_decode_failed")
    assert "application/dicom" not in resp.headers["content-type"]
    dcmread.assert_not_called()
    pixel_array.assert_not_called()


def test_whole_object_path_unchanged_for_unsupported_syntax() -> None:
    """AC 8 guard: without ``frame`` an unsupported syntax is returned byte-for-byte."""
    data = build_compressed("1.2.840.10008.1.2.4.50")
    attachment = _attachment(data)
    client = _client(attachment, FakeObjectStore(data))

    resp = client.get(f"/dicom/studies/{attachment.id}")

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/dicom"
    assert resp.content == data


class _Tally:
    total = 0


@contextmanager
def _counting_decompressor() -> Iterator[_Tally]:
    """Count the bytes the helper's decompressor produces."""
    tally = _Tally()
    real = zlib.decompressobj

    class Counting:
        def __init__(self, *args: Any) -> None:
            self._inner = real(*args)

        def __getattr__(self, name: str) -> Any:
            return getattr(self._inner, name)

        def decompress(self, data: bytes, max_length: int = 0) -> bytes:
            out = self._inner.decompress(data, max_length)
            tally.total += len(out)
            return out

    with patch.object(dicom_support.zlib, "decompressobj", Counting):
        yield tally
