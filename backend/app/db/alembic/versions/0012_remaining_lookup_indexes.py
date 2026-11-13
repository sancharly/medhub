"""Indexes for the two lookups migration 0011 left scanning (SR-026 AC 6, PRB-021, TASK-220).

Adds btree indexes on ``attachment.clinical_entry_id`` (attachments of a clinical entry) and
``consent_grant(doctor_id, active)`` (a doctor's patients by active consent). The existing
``ix_consent_grant_patient_doctor_active`` leads with ``patient_id`` and cannot serve a lookup by
doctor.

Plain ``CREATE INDEX`` (not ``CONCURRENTLY``), as 0011: each statement takes a SHARE lock, which
blocks writes to that table, not reads, while the index builds. Deployment is a single host with a
maintenance window. Apply it to an existing database only with the operator's go-ahead.

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-14
"""

from __future__ import annotations

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_attachment_clinical_entry_id", "attachment", ["clinical_entry_id"])
    op.create_index("ix_consent_grant_doctor_id_active", "consent_grant", ["doctor_id", "active"])


def downgrade() -> None:
    op.drop_index("ix_consent_grant_doctor_id_active", table_name="consent_grant")
    op.drop_index("ix_attachment_clinical_entry_id", table_name="attachment")
