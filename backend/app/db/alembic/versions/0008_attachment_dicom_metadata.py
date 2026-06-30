"""Add dicom_metadata JSONB column to attachment (SR-013 TASK-045).

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "attachment",
        sa.Column("dicom_metadata", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("attachment", "dicom_metadata")
