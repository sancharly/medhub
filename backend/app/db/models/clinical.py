"""ClinicalEntry model — maps to FHIR Composition."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin, UUIDMixin


class ClinicalEntry(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "clinical_entry"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id", name="fk_clinical_entry_patient_id"), nullable=False
    )
    author_doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id", name="fk_clinical_entry_author_doctor_id"), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=False)
