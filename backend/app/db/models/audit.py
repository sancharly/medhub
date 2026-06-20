"""AuditLog model — append-only, no FK on actor_id (SR-023)."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, UUIDMixin


class AuditOutcome(enum.Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class AuditLog(UUIDMixin, Base):
    __tablename__ = "audit_log"

    # actor_id is NOT a FK — actor may be unknown for pre-auth events
    actor_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    action: Mapped[str] = mapped_column(nullable=False)
    target_type: Mapped[str | None] = mapped_column(nullable=True)
    target_id: Mapped[str | None] = mapped_column(nullable=True)
    outcome: Mapped[AuditOutcome] = mapped_column(
        SAEnum(AuditOutcome, name="auditoutcome"), nullable=False
    )
    ip: Mapped[str | None] = mapped_column(nullable=True)
    # Server-assigned timestamp — not from caller
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
