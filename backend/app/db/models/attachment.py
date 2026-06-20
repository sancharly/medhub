"""Attachment model — maps to FHIR DocumentReference / Binary."""

import uuid

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin, UUIDMixin


class Attachment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "attachment"

    clinical_entry_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinical_entry.id", name="fk_attachment_clinical_entry_id"), nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id", name="fk_attachment_patient_id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(nullable=False)
    content_type: Mapped[str] = mapped_column(nullable=False)
    size: Mapped[int] = mapped_column(BigInteger(), nullable=False)
    storage_key: Mapped[str] = mapped_column(nullable=False)
    checksum: Mapped[str] = mapped_column(nullable=False)
