"""Database repositories — typed data-access layer."""

from app.db.repositories.account_repo import AccountRepository as AccountRepository
from app.db.repositories.anonymized_dataset_repo import (
    AnonymizedDatasetRepository as AnonymizedDatasetRepository,
)
from app.db.repositories.appointment_repo import AppointmentRepository as AppointmentRepository
from app.db.repositories.attachment_repo import AttachmentRepository as AttachmentRepository
from app.db.repositories.audit_repo import AuditRepository as AuditRepository
from app.db.repositories.base import Repository as Repository
from app.db.repositories.clinical_repo import ClinicalRepository as ClinicalRepository
from app.db.repositories.consent_repo import ConsentRepository as ConsentRepository
from app.db.repositories.group_repo import GroupRepository as GroupRepository
from app.db.repositories.module_repo import ModuleRepository as ModuleRepository
from app.db.repositories.session import get_db as get_db
from app.db.repositories.session import get_engine as get_engine
from app.db.repositories.session import get_session_factory as get_session_factory
