"""FHIR mapping verification tests — programmatically check all fields from fhir-mapping.md."""

from app.db.models.account import Account
from app.db.models.anonymized_dataset import AnonymizedDataset
from app.db.models.appointment import Appointment
from app.db.models.attachment import Attachment
from app.db.models.clinical import ClinicalEntry
from app.db.models.consent import ConsentGrant


def _columns(model_class) -> set[str]:
    return {col.key for col in model_class.__table__.columns}


def test_account_fhir_fields():
    """Account must have all fields in fhir-mapping.md Account → Patient/Practitioner."""
    cols = _columns(Account)
    required = {"id", "email", "first_name", "surname", "date_of_birth", "user_type", "status"}
    assert required <= cols, f"Missing Account fields: {required - cols}"


def test_appointment_fhir_fields():
    """Appointment must have all fields in fhir-mapping.md Appointment → Appointment."""
    cols = _columns(Appointment)
    required = {"id", "scheduled_at", "state", "doctor_id", "patient_id"}
    assert required <= cols, f"Missing Appointment fields: {required - cols}"


def test_clinical_entry_fhir_fields():
    """ClinicalEntry must have all fields in fhir-mapping.md ClinicalEntry → Composition."""
    cols = _columns(ClinicalEntry)
    required = {"id", "patient_id", "author_doctor_id", "occurred_at", "description"}
    assert required <= cols, f"Missing ClinicalEntry fields: {required - cols}"


def test_attachment_fhir_fields():
    """Attachment must have all fields in fhir-mapping.md Attachment → DocumentReference."""
    cols = _columns(Attachment)
    required = {"filename", "content_type", "size", "checksum", "storage_key"}
    assert required <= cols, f"Missing Attachment fields: {required - cols}"


def test_consent_grant_fhir_fields():
    """ConsentGrant must have all fields in fhir-mapping.md ConsentGrant → Consent."""
    cols = _columns(ConsentGrant)
    required = {"patient_id", "doctor_id", "source_type", "active", "created_at", "revoked_at"}
    assert required <= cols, f"Missing ConsentGrant fields: {required - cols}"


def test_anonymized_dataset_no_plaintext_code():
    """AnonymizedDataset must not expose a 'code' column — only 'code_hash'."""
    cols = _columns(AnonymizedDataset)
    assert "code" not in cols
    assert "code_hash" in cols
