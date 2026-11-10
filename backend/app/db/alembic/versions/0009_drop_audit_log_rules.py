"""Drop the DO INSTEAD NOTHING rules on audit_log (SR-023 AC 8, ADR-0017).

The rules of 0006 turned an UPDATE or DELETE on audit_log into a silent success. Append-only is
now enforced by privilege: the runtime role has no UPDATE, DELETE or TRUNCATE on the table
(app.db.roles), so a refused statement fails with a permission error and the owner role can
still administer the table.

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-01
"""

from __future__ import annotations

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP RULE IF EXISTS no_delete_audit_log ON audit_log")
    op.execute("DROP RULE IF EXISTS no_update_audit_log ON audit_log")


def downgrade() -> None:
    op.execute("CREATE RULE no_update_audit_log AS ON UPDATE TO audit_log DO INSTEAD NOTHING")
    op.execute("CREATE RULE no_delete_audit_log AS ON DELETE TO audit_log DO INSTEAD NOTHING")
