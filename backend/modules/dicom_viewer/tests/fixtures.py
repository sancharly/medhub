"""Part-10 DICOM objects built in memory with pydicom and NumPy (CR-008, TASK-234)."""

from __future__ import annotations

import ctypes
import io
import random
import struct
import threading
import zlib
from collections.abc import Callable
from typing import Any

import numpy as np
import pydicom
import pytest
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.encaps import encapsulate
from pydicom.filereader import _read_file_meta_info, read_preamble
from pydicom.uid import (
    DeflatedExplicitVRLittleEndian,
    ExplicitVRBigEndian,
    ExplicitVRLittleEndian,
    ImplicitVRLittleEndian,
    RLELossless,
)

SECONDARY_CAPTURE = "1.2.840.10008.5.1.4.1.1.7"
# Fixed, so that the encoded length (and the pad byte after a deflate stream) is reproducible.
SOP_INSTANCE_UID = "1.2.826.0.1.3680043.8.498.1"


def _data_set(
    transfer_syntax: str | None,
    rows: int,
    columns: int,
    frames: int,
    samples_per_pixel: int,
    bits_allocated: int,
    pixel_representation: int,
) -> Dataset:
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = SECONDARY_CAPTURE
    meta.MediaStorageSOPInstanceUID = SOP_INSTANCE_UID
    if transfer_syntax is not None:
        meta.TransferSyntaxUID = transfer_syntax
    ds = Dataset()
    ds.file_meta = meta
    ds.SOPClassUID = SECONDARY_CAPTURE
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    ds.Rows = rows
    ds.Columns = columns
    ds.BitsAllocated = bits_allocated
    ds.BitsStored = bits_allocated
    ds.HighBit = bits_allocated - 1
    ds.PixelRepresentation = pixel_representation
    ds.SamplesPerPixel = samples_per_pixel
    ds.PhotometricInterpretation = "MONOCHROME2" if samples_per_pixel == 1 else "RGB"
    if samples_per_pixel > 1:
        ds.PlanarConfiguration = 0
    if frames != 1:
        ds.NumberOfFrames = frames
    return ds


def _write(ds: Dataset, **encoding: bool) -> bytes:
    buf = io.BytesIO()
    pydicom.dcmwrite(buf, ds, enforce_file_format=True, **encoding)
    return buf.getvalue()


def build_dicom(
    transfer_syntax: str | None = ExplicitVRLittleEndian,
    *,
    rows: int = 4,
    columns: int = 4,
    frames: int = 1,
    samples_per_pixel: int = 1,
    bits_allocated: int = 16,
    pixel_representation: int = 0,
) -> tuple[bytes, np.ndarray]:
    """An uncompressed object (Implicit, Explicit LE or BE, Deflated) and its expected array.

    ``transfer_syntax=None`` leaves (0002,0010) out of the file meta information.
    """
    ds = _data_set(
        ExplicitVRLittleEndian if transfer_syntax is None else transfer_syntax,
        rows,
        columns,
        frames,
        samples_per_pixel,
        bits_allocated,
        pixel_representation,
    )
    shape = [rows, columns] + ([samples_per_pixel] if samples_per_pixel > 1 else [])
    if frames != 1:
        shape = [frames, *shape]
    dtype = np.dtype(f"{'i' if pixel_representation else 'u'}{bits_allocated // 8}")
    count = int(np.prod(shape))
    values = np.arange(count) % 251
    if pixel_representation:
        values = values - 125  # signed objects carry negative samples too
    expected = values.astype(dtype).reshape(shape)
    if transfer_syntax == ExplicitVRBigEndian:
        pixel_bytes = expected.astype(dtype.newbyteorder(">")).tobytes()
    else:
        pixel_bytes = expected.astype(dtype.newbyteorder("<")).tobytes()
    ds.add_new(0x7FE00010, "OB" if bits_allocated == 8 else "OW", pixel_bytes)
    data = _write(ds)
    return (data if transfer_syntax is not None else _without_transfer_syntax(data)), expected


def build_rle(**kwargs: Any) -> tuple[bytes, np.ndarray]:
    """The object ``build_dicom`` describes, RLE Lossless encoded, and its expected array."""
    data, expected = build_dicom(ExplicitVRLittleEndian, **kwargs)
    ds = pydicom.dcmread(io.BytesIO(data))
    ds.compress(RLELossless)
    return _write(ds), expected


YBR_SAMPLES = np.array(
    [[10, 90, 200], [20, 80, 190], [30, 70, 180], [40, 60, 170]] * 2, dtype=np.uint8
).reshape(2, 4, 3)


def build_ybr(photometric: str, *, rle: bool = False) -> tuple[bytes, np.ndarray]:
    """A 2 x 4 colour object whose samples are stored as YCbCr, and the samples a client must get.

    ``YBR_FULL`` stores (Y, Cb, Cr) per pixel; ``YBR_FULL_422`` stores (Y1, Y2, Cb, Cr) for each
    pair of pixels, and the expected array repeats Cb and Cr for both pixels. Values are chosen so
    that a YCbCr to RGB conversion would change them.
    """
    ds = _data_set(ExplicitVRLittleEndian, 2, 4, 1, 3, 8, 0)
    ds.PhotometricInterpretation = photometric
    if photometric == "YBR_FULL_422":
        pairs = YBR_SAMPLES.reshape(2, 2, 2, 3)  # rows, pair, pixel-in-pair, sample
        stored = np.concatenate(
            [pairs[:, :, 0, :1], pairs[:, :, 1, :1], pairs[:, :, 0, 1:]], axis=2
        ).astype(np.uint8)
        expected = pairs.copy()
        expected[:, :, 1, 1:] = expected[:, :, 0, 1:]  # chroma is shared by the pair
        expected = expected.reshape(2, 4, 3)
        ds.PlanarConfiguration = 0
        raw = stored.tobytes()
    else:
        expected = YBR_SAMPLES
        raw = expected.tobytes()
    ds.add_new(0x7FE00010, "OB", raw)
    if rle:
        ds.compress(RLELossless)
    return _write(ds), expected


def build_frame_count_mismatch(declared: int | None, in_data: int) -> bytes:
    """A 2 x 2 8-bit object declaring ``declared`` frames (None: no NumberOfFrames) and holding
    ``in_data`` frames of pixel data."""
    ds = _data_set(ExplicitVRLittleEndian, 2, 2, 1, 1, 8, 0)
    if declared is not None:
        ds.NumberOfFrames = declared
    ds.add_new(0x7FE00010, "OB", bytes(range(1, 4 * in_data + 1)))
    return _write(ds)


def build_short_pixel_data(*, rows: int = 5, columns: int = 5) -> bytes:
    """An 8-bit object whose pixel data is one byte shorter than the header declares.

    The size is odd and the data is one byte short, so the even-length element needs no pad byte.
    """
    ds = _data_set(ExplicitVRLittleEndian, rows, columns, 1, 1, 8, 0)
    ds.add_new(0x7FE00010, "OB", bytes(rows * columns - 1))
    return _write(ds)


def _without_transfer_syntax(data: bytes) -> bytes:
    """Cut element (0002,0010) out of the file meta information and fix the group length."""
    start = data.index(b"\x02\x00\x10\x00UI")
    removed = 8 + int.from_bytes(data[start + 6 : start + 8], "little")
    group_length = int.from_bytes(data[140:144], "little") - removed
    length = group_length.to_bytes(4, "little")
    return data[:140] + length + data[144:start] + data[start + removed :]


def build_compressed(transfer_syntax: str, *, rows: int = 4, columns: int = 4) -> bytes:
    """A compressed-syntax object carrying arbitrary encapsulated pixel bytes.

    It is refused from the header, so the fragment is never decoded.
    """
    ds = _data_set(transfer_syntax, rows, columns, 1, 1, 16, 0)
    ds.add_new(0x7FE00010, "OB", encapsulate([b"\x00" * 16]))
    ds["PixelData"].is_undefined_length = True
    # the encoding is given because a private UID does not say what it is
    return _write(ds, implicit_vr=False, little_endian=True)


def build_deflate_bomb(inflated_bytes: int, *, incompressible_prefix: int = 0) -> bytes:
    """A Deflated object whose data set inflates to a little over ``inflated_bytes``.

    ``incompressible_prefix`` bytes of random data come first, so the deflate stream is longer than
    one chunk (the zeros that follow compress to almost nothing).

    pydicom deflates the zero-filled PixelData, so the object itself is a few kilobytes.
    """
    ds = _data_set(DeflatedExplicitVRLittleEndian, 4, 4, 1, 1, 8, 0)
    prefix = random.Random(0).randbytes(incompressible_prefix)  # makes the stream span many chunks
    ds.add_new(0x7FE00010, "OB", prefix + bytes(inflated_bytes))
    return _write(ds)


def file_meta_end(data: bytes) -> int:
    """Offset of the first byte after group 0002."""
    fp = io.BytesIO(data)
    read_preamble(fp, False)
    _read_file_meta_info(fp)
    return fp.tell()


def build_corrupt_deflate() -> bytes:
    """A Deflated object whose raw-deflate stream is garbage (an invalid block type)."""
    data, _ = build_dicom(DeflatedExplicitVRLittleEndian)
    return data[: file_meta_end(data)] + b"\xff" * 64


def build_large_deflated(*, pad_byte: bool) -> tuple[bytes, np.ndarray]:
    """A valid Deflated object inflating over one 64 KiB chunk, with or without the pad byte.

    pydicom pads the data set to an even length, so a deflate stream of odd length is followed by
    one pad byte. The width is searched, with the fixed UID, until the stream has the wanted parity.
    """
    for columns in range(256, 320):
        data, expected = build_dicom(DeflatedExplicitVRLittleEndian, rows=256, columns=columns)
        decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
        decompressor.decompress(data[file_meta_end(data) :])
        if bool(decompressor.unused_data) == pad_byte:
            assert expected.nbytes > 64 * 1024
            return data, expected
    raise AssertionError("no object with the wanted pad byte")


def element(group: int, elem: int, vr: bytes, value: bytes) -> bytes:
    """One explicit VR little endian element with a 2-byte length."""
    return struct.pack("<HH", group, elem) + vr + struct.pack("<H", len(value)) + value


def with_file_meta_element(raw_element: bytes) -> bytes:
    """Preamble, ``DICM`` and a group 0002 holding only ``raw_element``."""
    return bytes(128) + b"DICM" + raw_element


def call_with_timeout(call: Callable[[], Any], seconds: float = 10) -> Any:
    """Run ``call`` in a thread; fail the test if it does not return, so a hang is not a stall.

    The spinning call is interrupted with an exception in its thread, so it does not starve the
    rest of the run; a call that waits on another thread (the HTTP client) cannot be interrupted.
    """
    outcome: list[Any] = []
    failure: list[BaseException] = []

    def target() -> None:
        try:
            outcome.append(call())
        except BaseException as exc:  # noqa: BLE001 - re-raised in the caller's thread
            failure.append(exc)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(seconds)
    if thread.is_alive():
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_ulong(thread.ident or 0), ctypes.py_object(TimeoutError)
        )
        pytest.fail(f"call did not return within {seconds} s")
    if failure:
        raise failure[0]
    return outcome[0] if outcome else None


__all__ = [
    "ImplicitVRLittleEndian",
    "build_compressed",
    "build_corrupt_deflate",
    "build_deflate_bomb",
    "build_dicom",
    "build_frame_count_mismatch",
    "build_rle",
    "build_short_pixel_data",
    "build_ybr",
    "build_large_deflated",
    "call_with_timeout",
    "element",
    "with_file_meta_element",
    "file_meta_end",
]
