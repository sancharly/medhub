"""DICOM checks shared by the DICOM viewer module and upload validation (CR-008 D-B).

Two pydicom-facing checks that must run before any data set is parsed or decoded:

* ``read_transfer_syntax`` reads the transfer syntax UID from the file meta information only.
* ``check_inflated_size`` counts, with a bounded decompressor, what a Deflated object inflates to.

No FastAPI or problem types here: each caller maps the exceptions to its own problem. The read of
the file meta information uses pydicom's private ``_read_file_meta_info`` (SOUP-015 1.3); a test
(TC-019.6) fails if it changes.
"""

from __future__ import annotations

import zlib
from typing import BinaryIO

from pydicom.dataset import FileMetaDataset
from pydicom.filereader import _read_file_meta_info, read_preamble

__all__ = [
    "DeflateStreamError",
    "InflatedSizeExceeded",
    "check_inflated_size",
    "read_transfer_syntax",
]

CHUNK_SIZE = 64 * 1024


class InflatedSizeExceeded(Exception):
    """A Deflated object inflates to more than the allowed number of bytes."""


class DeflateStreamError(Exception):
    """The deflate stream of a Deflated object is corrupt or truncated."""


def _read_file_meta(fp: BinaryIO) -> FileMetaDataset | None:
    """Read the preamble and group 0002; leave ``fp`` after it. ``None`` if unreadable."""
    try:
        read_preamble(fp, False)
        return _read_file_meta_info(fp)
    except Exception:  # noqa: BLE001 - no preamble or a broken group 0002 means "none declared"
        return None


def read_transfer_syntax(fp: BinaryIO) -> str | None:
    """Return the transfer syntax UID from the file meta information, leaving ``fp`` at offset 0.

    ``None`` when there is no preamble, no readable group 0002 or no (0002,0010). Nothing beyond
    group 0002 is parsed and no encoding is inferred.
    """
    try:
        fp.seek(0)
        meta = _read_file_meta(fp)
        if meta is None:
            return None
        uid = meta.get("TransferSyntaxUID")
        return str(uid) if uid else None
    except Exception:  # noqa: BLE001 - an element pydicom cannot convert (unknown VR, bad length)
        return None
    finally:
        fp.seek(0)


def check_inflated_size(fp: BinaryIO, limit: int) -> None:
    """Raise ``InflatedSizeExceeded`` if the Deflated data set in ``fp`` inflates above ``limit``.

    The caller has established that the transfer syntax is Deflated Explicit VR Little Endian. The
    raw-deflate stream after group 0002 is read in 64 KiB chunks and inflated at most 64 KiB per
    call; the output is counted and discarded, so memory stays at one input and one output chunk.
    ``DeflateStreamError`` for a corrupt or truncated stream. ``fp`` is left at offset 0.
    """
    try:
        fp.seek(0)
        if _read_file_meta(fp) is None:
            raise DeflateStreamError("The file meta information is not readable.")
        decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
        total = 0
        try:
            while not decompressor.eof:
                chunk = fp.read(CHUNK_SIZE)
                if not chunk:
                    raise DeflateStreamError("The deflate stream is truncated.")
                pending = chunk
                while True:
                    out = decompressor.decompress(pending, CHUNK_SIZE)
                    total += len(out)
                    if total > limit:
                        raise InflatedSizeExceeded(f"Inflates to more than {limit} bytes.")
                    pending = decompressor.unconsumed_tail
                    # after the end of the stream a pad byte may stay in the tail: stop there
                    if decompressor.eof or (not out and not pending):
                        break
        except zlib.error as exc:
            raise DeflateStreamError(str(exc)) from exc
    finally:
        fp.seek(0)
