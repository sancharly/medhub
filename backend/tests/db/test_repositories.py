"""Repository CRUD round-trip tests (TASK-012)."""

from datetime import UTC, datetime

from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.anonymized_dataset import AnonymizedDataset
from app.db.models.appointment import Appointment, AppointmentState
from app.db.models.attachment import Attachment
from app.db.models.clinical import ClinicalEntry
from app.db.models.consent import ConsentGrant, ConsentSourceType
from app.db.models.group import Group, GroupMembership, MembershipSource
from app.db.models.module import ModuleRegistry
from app.db.repositories.account_repo import AccountRepository
from app.db.repositories.anonymized_dataset_repo import AnonymizedDatasetRepository
from app.db.repositories.appointment_repo import AppointmentRepository
from app.db.repositories.attachment_repo import AttachmentRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.clinical_repo import ClinicalRepository
from app.db.repositories.consent_repo import ConsentRepository
from app.db.repositories.group_repo import GroupRepository
from app.db.repositories.module_repo import ModuleRepository


def _now() -> datetime:
    return datetime.now(UTC)


def _add_account(session, email: str, user_type: UserType = UserType.PATIENT) -> Account:
    acc = Account(email=email, user_type=user_type, status=AccountStatus.ACTIVE)
    session.add(acc)
    session.flush()
    return acc


# --- AccountRepository ---


def test_account_get_by_id(db_session):
    repo = AccountRepository(db_session)
    acc = _add_account(db_session, "getbyid@example.com")
    fetched = repo.get_by_id(acc.id)
    assert fetched is not None
    assert fetched.id == acc.id


def test_account_get_by_email(db_session):
    repo = AccountRepository(db_session)
    _add_account(db_session, "byemail@example.com")
    result = repo.get_by_email("byemail@example.com")
    assert result is not None
    assert result.email == "byemail@example.com"


def test_account_get_by_email_missing_returns_none(db_session):
    repo = AccountRepository(db_session)
    assert repo.get_by_email("nobody@example.com") is None


def test_account_get_by_email_sql_metacharacter(db_session):
    """Parameterized query must not match via SQL injection attempt."""
    repo = AccountRepository(db_session)
    result = repo.get_by_email("x' OR '1'='1")
    assert result is None


def test_account_list(db_session):
    repo = AccountRepository(db_session)
    _add_account(db_session, "list1@example.com")
    _add_account(db_session, "list2@example.com")
    accounts = repo.list()
    emails = {a.email for a in accounts}
    assert "list1@example.com" in emails
    assert "list2@example.com" in emails


def test_account_add(db_session):
    repo = AccountRepository(db_session)
    acc = Account(email="add@example.com", user_type=UserType.ADMIN, status=AccountStatus.ACTIVE)
    added = repo.add(acc)
    assert added.id is not None
    assert repo.get_by_id(added.id) is not None


# --- AppointmentRepository ---


def test_appointment_add_and_get(db_session):
    doctor = _add_account(db_session, "appt_doc_r@example.com", UserType.DOCTOR)
    patient = _add_account(db_session, "appt_pat_r@example.com")
    repo = AppointmentRepository(db_session)
    appt = Appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        scheduled_at=_now(),
        state=AppointmentState.PENDING,
    )
    added = repo.add(appt)
    fetched = repo.get(added.id)
    assert fetched is not None
    assert fetched.doctor_id == doctor.id


def test_list_for_doctor_excludes_other_doctors(db_session):
    doc1 = _add_account(db_session, "doc1_r@example.com", UserType.DOCTOR)
    doc2 = _add_account(db_session, "doc2_r@example.com", UserType.DOCTOR)
    patient = _add_account(db_session, "shared_pat_r@example.com")
    repo = AppointmentRepository(db_session)
    repo.add(
        Appointment(
            doctor_id=doc1.id,
            patient_id=patient.id,
            scheduled_at=_now(),
            state=AppointmentState.PENDING,
        )
    )
    repo.add(
        Appointment(
            doctor_id=doc2.id,
            patient_id=patient.id,
            scheduled_at=_now(),
            state=AppointmentState.PENDING,
        )
    )
    doc1_appts = repo.list_for_doctor(doc1.id)
    assert all(a.doctor_id == doc1.id for a in doc1_appts)
    assert not any(a.doctor_id == doc2.id for a in doc1_appts)


def test_list_for_patient(db_session):
    doctor = _add_account(db_session, "doc_lp_r@example.com", UserType.DOCTOR)
    pat1 = _add_account(db_session, "pat1_lp_r@example.com")
    pat2 = _add_account(db_session, "pat2_lp_r@example.com")
    repo = AppointmentRepository(db_session)
    repo.add(
        Appointment(
            doctor_id=doctor.id,
            patient_id=pat1.id,
            scheduled_at=_now(),
            state=AppointmentState.PENDING,
        )
    )
    repo.add(
        Appointment(
            doctor_id=doctor.id,
            patient_id=pat2.id,
            scheduled_at=_now(),
            state=AppointmentState.PENDING,
        )
    )
    pat1_appts = repo.list_for_patient(pat1.id)
    assert all(a.patient_id == pat1.id for a in pat1_appts)


# --- ClinicalRepository ---


def test_clinical_add_and_list(db_session):
    doctor = _add_account(db_session, "clin_doc_r@example.com", UserType.DOCTOR)
    patient = _add_account(db_session, "clin_pat_r@example.com")
    repo = ClinicalRepository(db_session)
    entry = ClinicalEntry(
        patient_id=patient.id,
        author_doctor_id=doctor.id,
        occurred_at=_now(),
        description="Test entry",
    )
    repo.add(entry)
    entries = repo.list_for_patient(patient.id)
    assert any(e.description == "Test entry" for e in entries)


# --- AttachmentRepository ---


def test_attachment_add_and_list(db_session):
    doctor = _add_account(db_session, "att_doc_r@example.com", UserType.DOCTOR)
    patient = _add_account(db_session, "att_pat_r@example.com")
    clin_repo = ClinicalRepository(db_session)
    entry = clin_repo.add(
        ClinicalEntry(
            patient_id=patient.id,
            author_doctor_id=doctor.id,
            occurred_at=_now(),
            description="With attachment",
        )
    )
    att_repo = AttachmentRepository(db_session)
    att_repo.add(
        Attachment(
            clinical_entry_id=entry.id,
            patient_id=patient.id,
            filename="scan.dcm",
            content_type="application/dicom",
            size=1024,
            storage_key="bucket/scan.dcm",
            checksum="xyz",
        )
    )
    results = att_repo.list_for_clinical_entry(entry.id)
    assert any(a.filename == "scan.dcm" for a in results)


# --- ConsentRepository ---


def test_consent_add_and_list_active(db_session):
    doctor = _add_account(db_session, "cg_doc_r@example.com", UserType.DOCTOR)
    patient = _add_account(db_session, "cg_pat_r@example.com")
    repo = ConsentRepository(db_session)
    repo.add(
        ConsentGrant(
            patient_id=patient.id,
            doctor_id=doctor.id,
            source_type=ConsentSourceType.MANUAL,
            active=True,
        )
    )
    active = repo.list_active_for_patient_doctor(patient.id, doctor.id)
    assert len(active) >= 1
    assert all(c.active for c in active)


def test_consent_inactive_excluded_from_active_list(db_session):
    doctor = _add_account(db_session, "cgx_doc_r@example.com", UserType.DOCTOR)
    patient = _add_account(db_session, "cgx_pat_r@example.com")
    repo = ConsentRepository(db_session)
    repo.add(
        ConsentGrant(
            patient_id=patient.id,
            doctor_id=doctor.id,
            source_type=ConsentSourceType.MANUAL,
            active=False,
        )
    )
    active = repo.list_active_for_patient_doctor(patient.id, doctor.id)
    assert len(active) == 0


# --- GroupRepository ---


def test_group_add_and_membership(db_session):
    acc = _add_account(db_session, "grp_member_r@example.com")
    repo = GroupRepository(db_session)
    g = repo.add(Group(name="Test Group"))
    membership = GroupMembership(group_id=g.id, account_id=acc.id, source=MembershipSource.MANUAL)
    repo.add_membership(membership)
    fetched = repo.get_membership(g.id, acc.id)
    assert fetched is not None
    assert fetched.source == MembershipSource.MANUAL


# --- ModuleRepository ---


def test_module_get_by_key(db_session):
    repo = ModuleRepository(db_session)
    mod = repo.add(ModuleRegistry(module_key="test_mod", name="Test Module", version="1.0.0"))
    fetched = repo.get_by_key("test_mod")
    assert fetched is not None
    assert fetched.id == mod.id


def test_module_set_enablement(db_session):
    g = Group(name="Enablement Group")
    db_session.add(g)
    db_session.flush()
    repo = ModuleRepository(db_session)
    mod = repo.add(ModuleRegistry(module_key="enmod", name="Enabled Module", version="1.0.0"))
    e = repo.set_enablement(g.id, mod.id, enabled=True)
    assert e.enabled is True
    e2 = repo.set_enablement(g.id, mod.id, enabled=False)
    assert e2.enabled is False


# --- AuditRepository — add only ---


def test_audit_repo_has_no_get_list_update_delete():
    """SR-023.5 immutability: AuditRepository must only expose add()."""
    assert not hasattr(AuditRepository, "get")
    assert not hasattr(AuditRepository, "list")
    assert not hasattr(AuditRepository, "update")
    assert not hasattr(AuditRepository, "delete")
    assert hasattr(AuditRepository, "add")


# --- AnonymizedDatasetRepository ---


def test_anonymized_dataset_get_by_code_hash(db_session):
    repo = AnonymizedDatasetRepository(db_session)
    ds = repo.add(
        AnonymizedDataset(
            code_hash="testhash123",
            payload={"key": "value"},
            created_at=_now(),
            retention_deadline=datetime(2031, 1, 1, tzinfo=UTC),
        )
    )
    fetched = repo.get_by_code_hash("testhash123")
    assert fetched is not None
    assert fetched.id == ds.id


def test_anonymized_dataset_get_by_code_hash_missing(db_session):
    repo = AnonymizedDatasetRepository(db_session)
    assert repo.get_by_code_hash("nonexistent") is None
