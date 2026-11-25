"""Tests for DICOM validation (TASK-045) and its inflation bound (TASK-240, TC-007.18).

The objects are built by the DICOM viewer module's fixtures, loaded by path because the module's
own ``tests`` package shadows ``backend/tests`` (as in ``tests/modules/test_dicom_support.py``).
"""

from __future__ import annotations

import importlib.util
import io
import tempfile
import uuid
import zlib
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydicom.uid import DeflatedExplicitVRLittleEndian, ExplicitVRLittleEndian, JPEGBaseline8Bit

from app.api.errors import ValidationProblem
from app.attachments.dicom_validation import validate_dicom
from app.attachments.service import AttachmentService
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.attachment import Attachment
from app.db.models.clinical import ClinicalEntry

_spec = importlib.util.spec_from_file_location(
    "dicom_viewer_fixtures",
    Path(__file__).parents[2] / "modules" / "dicom_viewer" / "tests" / "fixtures.py",
)
assert _spec is not None and _spec.loader is not None
fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fixtures)

LIMIT = 1024 * 1024
CHUNK = 64 * 1024


def test_invalid_dicom_raises_validation_problem() -> None:
    """Non-DICOM bytes raise ValidationProblem."""
    with pytest.raises(ValidationProblem):
        validate_dicom(io.BytesIO(b"not a dicom file"))


def test_valid_dicom_returns_metadata() -> None:
    """Valid DICOM returns dict with modality, patient_id, study_date."""
    mock_dataset = MagicMock()
    mock_dataset.Modality = "CT"
    mock_dataset.PatientID = "P001"
    mock_dataset.StudyDate = "20240101"

    with patch("pydicom.dcmread", return_value=mock_dataset):
        result = validate_dicom(io.BytesIO(b"fake dicom bytes"))

    assert result["modality"] == "CT"
    assert result["patient_id"] == "P001"
    assert result["study_date"] == "20240101"


def test_dicom_with_none_attributes_returns_none_for_absent_fields() -> None:
    """DICOM whose optional tags are None returns None for those fields."""
    mock_dataset = MagicMock()
    mock_dataset.Modality = None
    mock_dataset.PatientID = None
    mock_dataset.StudyDate = None

    with patch("pydicom.dcmread", return_value=mock_dataset):
        result = validate_dicom(io.BytesIO(b"fake bytes"))

    assert "modality" in result
    assert result["modality"] is None
    assert result["patient_id"] is None
    assert result["study_date"] is None


def test_dicom_validation_reads_header_from_file() -> None:
    """SR-013 AC 1/6: the header is read from the file object, not pixels; it is rewound."""
    fp = io.BytesIO(b"fake dicom bytes")
    mock_dataset = MagicMock()
    mock_dataset.Modality = "MR"
    mock_dataset.PatientID = None
    mock_dataset.StudyDate = None

    def fake_dcmread(arg, **kwargs):
        assert arg is fp
        assert kwargs == {"stop_before_pixels": True}
        arg.read(4)  # the parser consumed part of the file
        return mock_dataset

    with patch("pydicom.dcmread", side_effect=fake_dcmread):
        result = validate_dicom(fp)

    assert result["modality"] == "MR"
    assert fp.tell() == 0


# --- TASK-240: the inflation of a Deflated upload is bounded before validation (TC-007.18) ---


@contextmanager
def _decoded_limit(limit: int = LIMIT) -> Iterator[None]:
    """Make ``dicom_max_decoded_bytes()`` answer ``limit`` without touching the environment."""
    with patch(
        "app.modules.module_settings.get_settings",
        return_value=SimpleNamespace(dicom_max_decoded_bytes=limit),
    ):
        yield


@contextmanager
def _inflation_spy() -> Iterator[list[int]]:
    """The output size of every zlib inflation call, whoever makes it (helper or pydicom)."""
    sizes: list[int] = []
    real_decompress = zlib.decompress
    real_obj = zlib.decompressobj

    class Counting:
        def __init__(self, *args: Any) -> None:
            self._inner = real_obj(*args)

        def __getattr__(self, name: str) -> Any:
            return getattr(self._inner, name)

        def decompress(self, data: bytes, max_length: int = 0) -> bytes:
            out = self._inner.decompress(data, max_length)
            sizes.append(len(out))
            return out

    def counting_decompress(*args: Any, **kwargs: Any) -> bytes:
        out = real_decompress(*args, **kwargs)
        sizes.append(len(out))
        return out

    with (
        patch.object(zlib, "decompressobj", Counting),
        patch.object(zlib, "decompress", counting_decompress),
    ):
        yield sizes


def _bomb() -> bytes:
    """Inflates to 8 MiB against a 1 MiB bound; the object itself is small."""
    return fixtures.build_deflate_bomb(8 * LIMIT)


def _make_account(user_type: UserType) -> Account:
    return Account(
        id=uuid.uuid4(), email="u@example.com", user_type=user_type, status=AccountStatus.ACTIVE
    )


def _service() -> tuple[AttachmentService, MagicMock, Account, ClinicalEntry]:
    patient = _make_account(UserType.PATIENT)
    entry = ClinicalEntry(
        id=uuid.uuid4(),
        patient_id=patient.id,
        author_doctor_id=uuid.uuid4(),
        occurred_at=datetime.now(UTC),
        description="Test",
    )
    attachment_repo = MagicMock()
    attachment_repo.add.return_value = Attachment(
        id=uuid.uuid4(),
        clinical_entry_id=entry.id,
        patient_id=entry.patient_id,
        filename="x.dcm",
        content_type="application/dicom",
        size=1,
        storage_key="k",
        checksum="c",
    )
    clinical_repo = MagicMock()
    clinical_repo.get.return_value = entry
    consent = MagicMock()
    consent.has_active_grant.return_value = True
    storage = MagicMock()
    svc = AttachmentService(
        attachment_repo,
        clinical_repo,
        MagicMock(),
        AuthorizationService(consent, MagicMock()),
        storage,
    )
    return svc, storage, _make_account(UserType.DOCTOR), entry


def _store(svc: AttachmentService, actor: Account, entry: ClinicalEntry, data: bytes) -> Any:
    return svc.store(actor, entry.id, "x.dcm", "application/dicom", io.BytesIO(data))


def test_deflate_bomb_upload_refused_and_nothing_stored() -> None:
    """SR-013 AC 6: refused from the bounded count, never inflated whole, nothing stored."""
    svc, storage, doctor, entry = _service()

    with (
        _decoded_limit(),
        _inflation_spy() as sizes,
        patch("pydicom.dcmread") as dcmread,
        pytest.raises(ValidationProblem) as excinfo,
    ):
        fixtures.call_with_timeout(lambda: _store(svc, doctor, entry, _bomb()))

    problem = excinfo.value
    assert problem.status == 400
    assert problem.errors is not None
    assert [(e.field, e.rule) for e in problem.errors] == [("file", "dicom_decoded_size_exceeded")]
    assert str(LIMIT) in problem.errors[0].message
    dcmread.assert_not_called()
    storage.put_object.assert_not_called()
    assert sizes and max(sizes) <= CHUNK  # no unbounded inflation anywhere


def test_deflate_bomb_through_validate_dicom_on_a_spooled_file() -> None:
    """The upload route hands over a ``SpooledTemporaryFile``; it is read in bounded chunks."""
    reads: list[int] = []

    class Spy(tempfile.SpooledTemporaryFile):  # type: ignore[type-arg]
        def read(self, size: int = -1) -> bytes:
            data = super().read(size)
            reads.append(len(data))
            return data

    with Spy(max_size=1024) as fp:
        fp.write(_bomb())
        fp.seek(0)
        with _decoded_limit(), pytest.raises(ValidationProblem):
            fixtures.call_with_timeout(lambda: validate_dicom(fp))
        assert fp.tell() == 0
    assert reads and max(reads) <= CHUNK


def test_deflated_upload_within_bound_is_accepted() -> None:
    data, _ = fixtures.build_dicom(DeflatedExplicitVRLittleEndian, rows=64, columns=64)
    fp = io.BytesIO(data)

    with _decoded_limit():
        result = validate_dicom(fp)

    assert set(result) == {"modality", "patient_id", "study_date"}
    assert fp.tell() == 0


@pytest.mark.parametrize("pad_byte", [False, True], ids=["no_pad_byte", "pad_byte"])
def test_deflated_upload_over_one_chunk_is_accepted(pad_byte: bool) -> None:
    """An odd-length stream with a pad byte, inflating over one chunk, used to hang (TC-019.7)."""
    data, _ = fixtures.build_large_deflated(pad_byte=pad_byte)
    fp = io.BytesIO(data)

    with _decoded_limit():
        result = fixtures.call_with_timeout(lambda: validate_dicom(fp))

    assert "modality" in result
    assert fp.tell() == 0


def test_corrupt_deflate_stream_upload_refused() -> None:
    svc, storage, doctor, entry = _service()

    with _decoded_limit(), pytest.raises(ValidationProblem) as excinfo:
        _store(svc, doctor, entry, fixtures.build_corrupt_deflate())

    assert excinfo.value.status == 400
    assert "Invalid DICOM file" in str(excinfo.value)
    storage.put_object.assert_not_called()


@pytest.mark.filterwarnings("ignore:Expected implicit VR:UserWarning")
@pytest.mark.parametrize("vr, value", [(b"ZZ", b"1.2.840.10008.1.2.1\x00"), (b"UV", b"\x01\x02")])
def test_malformed_transfer_syntax_element_is_a_400_not_a_500(vr: bytes, value: bytes) -> None:
    data = fixtures.with_file_meta_element(fixtures.element(2, 0x10, vr, value))
    with _decoded_limit(), pytest.raises(ValidationProblem):
        fixtures.call_with_timeout(lambda: validate_dicom(io.BytesIO(data)))


@pytest.mark.parametrize("syntax", [ExplicitVRLittleEndian, JPEGBaseline8Bit])
def test_non_deflated_upload_unchanged(syntax: str) -> None:
    """Any other transfer syntax is stored as before and the inflation check is not called."""
    if syntax == ExplicitVRLittleEndian:
        data, _ = fixtures.build_dicom(syntax)
    else:
        data = fixtures.build_compressed(syntax)
    fp = io.BytesIO(data)

    with (
        _decoded_limit(),
        patch("app.attachments.dicom_validation.check_inflated_size") as check,
    ):
        result = validate_dicom(fp)

    check.assert_not_called()
    assert set(result) == {"modality", "patient_id", "study_date"}
    assert fp.tell() == 0
