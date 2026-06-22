"""InAppNotification model — in-app notification for appointment events (TASK-050)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin, UUIDMixin


class InAppNotification(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "in_app_notification"

    recipient_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id", name="fk_in_app_notification_recipient_account_id"),
        nullable=False,
    )
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("appointment.id", name="fk_in_app_notification_appointment_id"),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="QUEUED")
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
