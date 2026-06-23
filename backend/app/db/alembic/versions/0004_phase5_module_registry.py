"""Phase 5: add required_permissions and discovered_at to module_registry.

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "module_registry",
        sa.Column(
            "required_permissions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column(
        "module_registry",
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("module_registry", "discovered_at")
    op.drop_column("module_registry", "required_permissions")
