"""Account model — maps to FHIR Patient / Practitioner."""

import enum
from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin, UUIDMixin


class UserType(enum.Enum):
    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"
    ADMIN = "ADMIN"
    SYSADMIN = "SYSADMIN"


class AccountStatus(enum.Enum):
    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    DEACTIVATED = "DEACTIVATED"
    DELETED = "DELETED"


class Account(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "account"
    __table_args__ = (
        sa.UniqueConstraint("email", name="uq_account_email"),
        sa.Index("ix_account_email", "email"),
    )

    email: Mapped[str] = mapped_column(nullable=False)
    password_hash: Mapped[str | None] = mapped_column(nullable=True)
    user_type: Mapped[UserType] = mapped_column(SAEnum(UserType, name="usertype"), nullable=False)
    status: Mapped[AccountStatus] = mapped_column(
        SAEnum(AccountStatus, name="accountstatus"), nullable=False
    )
    first_name: Mapped[str | None] = mapped_column(nullable=True)
    surname: Mapped[str | None] = mapped_column(nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(nullable=True)
    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fhir_extensions: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)

    # Activation token — sha256 hash of raw token; raw token is emailed only
    activation_token_hash: Mapped[str | None] = mapped_column(nullable=True)
    activation_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
