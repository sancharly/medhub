"""PasswordHistory model — stores hashed past passwords to enforce history policy."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, UUIDMixin


class PasswordHistory(UUIDMixin, Base):
    __tablename__ = "password_history"

    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id", name="fk_password_history_account_id"),
        nullable=False,
        index=True,
    )
    # Argon2id hash — never plaintext
    password_hash: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
