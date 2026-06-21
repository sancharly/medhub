"""AnonymizedDataset model — stores KDF hash, never plaintext code."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, UUIDMixin


class AnonymizedDataset(UUIDMixin, Base):
    __tablename__ = "anonymized_dataset"

    # Argon2id KDF hash — plaintext code is never stored
    code_hash: Mapped[str] = mapped_column(nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # retention_deadline = created_at + 5 years; set by application layer
    retention_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
