"""Phase 2: password_history table + account activation token columns.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-21
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add activation token columns to account
    op.add_column("account", sa.Column("activation_token_hash", sa.String(), nullable=True))
    op.add_column(
        "account",
        sa.Column("activation_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create password_history table
    op.create_table(
        "password_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["account.id"], name="fk_password_history_account_id"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_password_history_account_id", "password_history", ["account_id"])


def downgrade() -> None:
    op.drop_index("ix_password_history_account_id", table_name="password_history")
    op.drop_table("password_history")
    op.drop_column("account", "activation_token_expires_at")
    op.drop_column("account", "activation_token_hash")
