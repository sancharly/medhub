"""Group and GroupMembership models."""

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.account import UserType
from app.db.models.base import Base, TimestampMixin, UUIDMixin


class MembershipSource(enum.Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class Group(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "group"

    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    auto_user_type: Mapped[UserType | None] = mapped_column(
        SAEnum(UserType, name="usertype"), nullable=True
    )


class GroupMembership(Base):
    __tablename__ = "group_membership"

    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("group.id", name="fk_group_membership_group_id"),
        primary_key=True,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id", name="fk_group_membership_account_id"),
        primary_key=True,
    )
    source: Mapped[MembershipSource] = mapped_column(
        SAEnum(MembershipSource, name="membershipsource"), nullable=False
    )
