"""Appointment model — maps to FHIR Appointment."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin, UUIDMixin


class AppointmentState(enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    DECLINED = "DECLINED"


class Appointment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "appointment"
    __table_args__ = (
        Index("ix_appointment_doctor_id", "doctor_id"),
        Index("ix_appointment_patient_id", "patient_id"),
    )

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id", name="fk_appointment_doctor_id"), nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id", name="fk_appointment_patient_id"), nullable=False
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    state: Mapped[AppointmentState] = mapped_column(
        SAEnum(AppointmentState, name="appointmentstate"), nullable=False
    )
