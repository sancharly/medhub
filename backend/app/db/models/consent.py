"""ConsentGrant model — maps to FHIR Consent."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin, UUIDMixin


class ConsentSourceType(enum.Enum):
    MANUAL = "MANUAL"
    APPOINTMENT = "APPOINTMENT"


class ConsentGrant(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "consent_grant"
    __table_args__ = (
        Index("ix_consent_grant_patient_doctor_active", "patient_id", "doctor_id", "active"),
    )

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id", name="fk_consent_grant_patient_id"), nullable=False
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id", name="fk_consent_grant_doctor_id"), nullable=False
    )
    source_type: Mapped[ConsentSourceType] = mapped_column(
        SAEnum(ConsentSourceType, name="consentsourcetype"), nullable=False
    )
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("appointment.id", name="fk_consent_grant_appointment_id"), nullable=True
    )
    active: Mapped[bool] = mapped_column(nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
