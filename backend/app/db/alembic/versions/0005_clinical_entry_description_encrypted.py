"""Alter clinical_entry.description to String for EncryptedString TypeDecorator.

EncryptedString uses String as its SQL impl (transparent encrypt-on-write /
decrypt-on-read via TypeDecorator). This migration converts the column from
Text to String so the storage type matches the declared ORM type (SR-022).

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "clinical_entry",
        "description",
        type_=sa.String(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "clinical_entry",
        "description",
        type_=sa.Text(),
        existing_nullable=False,
    )
