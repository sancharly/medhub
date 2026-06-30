"""Add unique constraint on group.name (SR-014 TASK-040a).

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-30
"""

from __future__ import annotations

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_group_name", "group", ["name"])


def downgrade() -> None:
    op.drop_constraint("uq_group_name", "group", type_="unique")
