"""SQLAlchemy domain models — import all models so metadata is populated."""

from app.db.models.account import Account as Account
from app.db.models.account import AccountStatus as AccountStatus
from app.db.models.account import UserType as UserType
from app.db.models.anonymized_dataset import AnonymizedDataset as AnonymizedDataset
from app.db.models.appointment import Appointment as Appointment
from app.db.models.appointment import AppointmentState as AppointmentState
from app.db.models.attachment import Attachment as Attachment
from app.db.models.audit import AuditLog as AuditLog
from app.db.models.audit import AuditOutcome as AuditOutcome
from app.db.models.base import Base as Base
from app.db.models.base import TimestampMixin as TimestampMixin
from app.db.models.base import UUIDMixin as UUIDMixin
from app.db.models.clinical import ClinicalEntry as ClinicalEntry
from app.db.models.consent import ConsentGrant as ConsentGrant
from app.db.models.consent import ConsentSourceType as ConsentSourceType
from app.db.models.group import Group as Group
from app.db.models.group import GroupMembership as GroupMembership
from app.db.models.group import MembershipSource as MembershipSource
from app.db.models.module import GroupModuleEnablement as GroupModuleEnablement
from app.db.models.module import ModuleRegistry as ModuleRegistry
