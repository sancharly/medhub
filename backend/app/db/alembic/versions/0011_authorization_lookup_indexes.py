"""Indexes for the four authorization lookups (SR-026 AC 6, PRB-021, TASK-219).

Adds plain btree indexes on ``appointment.scheduled_at``, ``consent_grant.appointment_id``,
``clinical_entry.patient_id`` and ``attachment.patient_id``, so the lookups by appointment time,
by consent appointment and by patient do not scan the table.

Plain ``CREATE INDEX`` (not ``CONCURRENTLY``): each statement takes a SHARE lock, which blocks
writes to that table, not reads, while the index builds. Deployment is a single host with a
maintenance window and the build is fast at this data size. Apply it to an existing database
only with the operator's go-ahead.

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-13
"""

from __future__ import annotations

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

_INDEXES = (
    ("ix_appointment_scheduled_at", "appointment", "scheduled_at"),
    ("ix_consent_grant_appointment_id", "consent_grant", "appointment_id"),
    ("ix_clinical_entry_patient_id", "clinical_entry", "patient_id"),
    ("ix_attachment_patient_id", "attachment", "patient_id"),
)


def upgrade() -> None:
    for name, table, column in _INDEXES:
        op.create_index(name, table, [column])


def downgrade() -> None:
    for name, table, _ in reversed(_INDEXES):
        op.drop_index(name, table_name=table)
