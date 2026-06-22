"""Phase 3: in_app_notification table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-21

All other Phase 3 tables (group, module_registry, group_membership, group_module_enablement,
appointment, clinical_entry, attachment, consent_grant) were already created in 0001_initial.
This migration adds only the in_app_notification table introduced in TASK-050.
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "in_app_notification",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("recipient_account_id", sa.UUID(), nullable=False),
        sa.Column("appointment_id", sa.UUID(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["recipient_account_id"],
            ["account.id"],
            name="fk_in_app_notification_recipient_account_id",
        ),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointment.id"],
            name="fk_in_app_notification_appointment_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("in_app_notification")
