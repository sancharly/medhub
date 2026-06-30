"""Add PostgreSQL RULEs to enforce append-only on audit_log (SR-023.5).

UPDATE and DELETE on audit_log are silently suppressed at the database level,
so no DB user (including the application role) can alter existing audit rows.
This is defense-in-depth beyond the Python-layer convention (no repository
update/delete methods).

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-30
"""

from __future__ import annotations

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE RULE no_update_audit_log AS ON UPDATE TO audit_log DO INSTEAD NOTHING")
    op.execute("CREATE RULE no_delete_audit_log AS ON DELETE TO audit_log DO INSTEAD NOTHING")


def downgrade() -> None:
    op.execute("DROP RULE IF EXISTS no_delete_audit_log ON audit_log")
    op.execute("DROP RULE IF EXISTS no_update_audit_log ON audit_log")
