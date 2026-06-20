"""ModuleRegistry and GroupModuleEnablement models."""

import uuid

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin, UUIDMixin


class ModuleRegistry(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "module_registry"
    __table_args__ = (sa.UniqueConstraint("module_key", name="uq_module_registry_module_key"),)

    module_key: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    version: Mapped[str] = mapped_column(nullable=False)


class GroupModuleEnablement(Base):
    __tablename__ = "group_module_enablement"

    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("group.id", name="fk_group_module_enablement_group_id"),
        primary_key=True,
    )
    module_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("module_registry.id", name="fk_group_module_enablement_module_id"),
        primary_key=True,
    )
    enabled: Mapped[bool] = mapped_column(nullable=False)
