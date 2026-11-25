"""TASK-235: ``?frame=N`` returns exactly frame N as ``application/octet-stream``.

SR-017 AC 8 and AC 9; TC-019.9 to TC-019.11.

Real objects built with pydicom and NumPy (``fixtures.py``) and really decoded: no stub, no spy.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pytest
from dicom_viewer.dicom import stream_dicom
from pydicom.uid import (
    DeflatedExplicitVRLittleEndian,
    ExplicitVRBigEndian,
    ExplicitVRLittleEndian,
    ImplicitVRLittleEndian,
)

from app.api.errors import ValidationProblem
from tests.fixtures import (
    build_compressed,
    build_dicom,
    build_frame_count_mismatch,
    build_rle,
    build_ybr,
)
from tests.test_size_bounds import FakeObjectStore, _assert_problem, _attachment, _client, _get

SHAPES: dict[str, dict[str, Any]] = {
    "8-bit unsigned single frame": {"bits_allocated": 8},
    "16-bit signed 3 frames": {"frames": 3, "bits_allocated": 16, "pixel_representation": 1},
    "8-bit RGB single frame": {"bits_allocated": 8, "samples_per_pixel": 3},
}


def _plain(syntax: str) -> Callable[..., tuple[bytes, np.ndarray]]:
    return lambda **kw: build_dicom(syntax, **kw)


BUILDERS: dict[str, Callable[..., tuple[bytes, np.ndarray]]] = {
    "implicit-le": _plain(ImplicitVRLittleEndian),
    "explicit-le": _plain(ExplicitVRLittleEndian),
    "deflated": _plain(DeflatedExplicitVRLittleEndian),
    "explicit-be": _plain(ExplicitVRBigEndian),
    "rle": build_rle,
}


def _native_bytes(frame: np.ndarray) -> bytes:
    return frame.astype(frame.dtype.newbyteorder("="), copy=False).tobytes()


def _frames(expected: np.ndarray, multi: bool) -> list[np.ndarray]:
    return list(expected) if multi else [expected]


@pytest.mark.parametrize("shape", SHAPES)
@pytest.mark.parametrize("syntax", BUILDERS)
def test_frame_bytes_equal_known_values(syntax: str, shape: str) -> None:
    """TC-019.9 (SR-017 AC 9): every supported syntax, single and multi frame, frame by frame."""
    kwargs = SHAPES[shape]
    data, expected = BUILDERS[syntax](**kwargs)
    attachment = _attachment(data)
    client = _client(attachment, FakeObjectStore(data))

    frames = _frames(expected, kwargs.get("frames", 1) != 1)
    for n, known in enumerate(frames):
        resp = _get(client, attachment, n)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/octet-stream"
        assert resp.content == _native_bytes(known)
    assert len({_native_bytes(f) for f in frames}) == len(frames)  # the frames differ


def test_signed_samples_are_two_complement_native_order() -> None:
    """TC-019.9: the layout of ADD-015, read back independently of the server code."""
    data, expected = build_dicom(ExplicitVRBigEndian, frames=3, pixel_representation=1)
    attachment = _attachment(data)

    resp = _get(_client(attachment, FakeObjectStore(data)), attachment, 1)

    decoded = np.frombuffer(resp.content, dtype=np.dtype("i2").newbyteorder("="))
    assert decoded.min() < 0
    assert decoded.tolist() == expected[1].reshape(-1).tolist()


@pytest.mark.parametrize("kwargs", [{"bits_allocated": 8}, {"frames": 3}])
def test_last_frame_and_out_of_range(kwargs: dict[str, Any]) -> None:
    """TC-019.11 (SR-017 AC 9): the last frame is served; one past it is the unchanged 400."""
    data, expected = build_dicom(ExplicitVRLittleEndian, **kwargs)
    frames = kwargs.get("frames", 1)
    attachment = _attachment(data)
    client = _client(attachment, FakeObjectStore(data))

    last = _get(client, attachment, frames - 1)
    assert last.status_code == 200
    assert last.content == _native_bytes(_frames(expected, frames != 1)[-1])

    over = _get(client, attachment, frames)
    _assert_problem(over)
    noun = "frame" if frames == 1 else "frames"
    assert over.json()["detail"] == (
        f"Frame {frames} out of range; this DICOM has {frames} {noun}."
    )
    assert "application/octet-stream" not in over.headers["content-type"]
    assert _native_bytes(_frames(expected, frames != 1)[-1]) not in over.content


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(lambda: build_dicom(ExplicitVRLittleEndian, frames=3)[0], id="uncompressed"),
        pytest.param(lambda: build_compressed("1.2.840.10008.1.2.4.50"), id="jpeg-baseline"),
    ],
)
def test_whole_object_is_byte_identical(build: Callable[[], bytes]) -> None:
    """TC-019.10 (SR-017 AC 8): without ``frame`` the stored object comes back as it was stored."""
    data = build()
    attachment = _attachment(data)

    resp = _client(attachment, FakeObjectStore(data)).get(f"/dicom/studies/{attachment.id}")

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/dicom"
    assert resp.content == data


@pytest.mark.parametrize(
    ("photometric", "rle"),
    [("YBR_FULL", False), ("YBR_FULL", True), ("YBR_FULL_422", False)],
    ids=["ybr-full", "ybr-full-rle", "ybr-full-422"],
)
def test_ycbcr_samples_are_served_as_stored(photometric: str, rle: bool) -> None:
    """TC-019.9 (SR-017 AC 9, CR-008 D-4): no YCbCr to RGB conversion; a YBR_FULL_422 object is
    served upsampled to 3 samples per pixel, interleaved, the chroma pair repeated."""
    data, expected = build_ybr(photometric, rle=rle)
    attachment = _attachment(data)

    resp = _get(_client(attachment, FakeObjectStore(data)), attachment, 0)

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/octet-stream"
    assert resp.content == expected.tobytes()
    assert len(resp.content) == 2 * 4 * 3


@pytest.mark.parametrize(
    ("declared", "in_data"),
    [(None, 3), (1, 3), (2, 3)],
    ids=["absent-excess-data", "one-excess-data", "two-data-for-three"],
)
def test_frame_count_disagreeing_with_the_data_is_refused(
    declared: int | None, in_data: int
) -> None:
    """TC-019.11 (SR-017 AC 9): the decoded array must be one frame, or NumberOfFrames frames, of
    the header's shape; otherwise no frame is returned, whichever frame is asked for."""
    data = build_frame_count_mismatch(declared, in_data)
    attachment = _attachment(data)
    client = _client(attachment, FakeObjectStore(data))

    for n in (0, 1, 2):
        resp = _get(client, attachment, n)
        _assert_problem(resp, "dicom_decode_failed")
        assert bytes(range(1, 13)) not in resp.content


def test_negative_frame_is_refused_before_decoding() -> None:
    """TC-019.11: the unit refuses a negative index."""
    data, _ = build_dicom(ExplicitVRLittleEndian, frames=3)

    with pytest.raises(ValidationProblem):
        stream_dicom(data, -1)
