---
id: "TASK-219"
type: task
title: "Indexes for the four authorization lookups (migration 0011) and the one-row activation guard"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-13"
links:
  - target: "SR-026"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-021"
    relation: relates_to
  - target: "PRB-022"
    relation: relates_to
  - target: "ADD-016"
    relation: relates_to
  - target: "SOUP-009"
    relation: relates_to
  - target: "SR-033"
    relation: relates_to
tags: ["cr:CR-006", "performance", "migration", "control:design"]
---

# TASK-219 — Indexes for the four authorization lookups (migration 0011) and the one-row activation guard

- **Software item / unit:** SI-PERSIST models and Alembic (ADD-016); SI-IDENTITY activation (regression test
  only).
- **PRB:** PRB-021; PRB-022 is `rejected` (D-1) and gets the SR-026 AC 6 regression test here. **CR:** CR-006.
- **Depends on:** none (parallel with the attachment chain).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** S (`backend/app/db/models/{appointment,consent,clinical,attachment}.py`, new
  `backend/app/db/alembic/versions/0011_authorization_lookup_indexes.py`; tests
  `backend/tests/db/test_migration_0011_indexes.py`, `backend/tests/identity/test_activation_one_row.py`;
  records TS-018).
- **Ask first:** applying 0011 to any existing database (it locks writes on four tables while the indexes
  build). The task runs it only on test databases.

## Objective

SR-026 AC 6: the lookups by appointment time, by consent appointment, and by patient for clinical entries and
attachments are served by an index (a query-plan check on a seeded database shows no sequential scan), and
validating an activation token reads at most one account row. No index exists today on
`appointment.scheduled_at`, `consent_grant.appointment_id`, `clinical_entry.patient_id`,
`attachment.patient_id` (models, migrations 0001 to 0010).

## Implementation detail

- `Index("ix_appointment_scheduled_at", "scheduled_at")`, `Index("ix_consent_grant_appointment_id",
  "appointment_id")`, `Index("ix_clinical_entry_patient_id", "patient_id")`,
  `Index("ix_attachment_patient_id", "patient_id")` in `__table_args__` (as `ix_appointment_patient_id`).
- Migration 0011: `op.create_index` × 4, `downgrade` drops them. Plain `CREATE INDEX` (the deployment is a
  single host with a maintenance window; `CONCURRENTLY` would need an autocommit block and is not needed at
  this data size). The deployment note (lock while building) goes to `infra/DEPLOY.md` via TASK-225.
- Model metadata and migration head agree (the existing `test_migration.py` autogenerate-diff check).

## Tests (write first)

- `test_upgrade_downgrade_0011_empty_and_populated` (SR-026 AC 6): upgrade from 0010 on an empty database and
  on one seeded with 10 000 appointments, consents, entries and attachments; downgrade back; row counts
  unchanged.
- `test_authorization_lookups_use_index` (SR-026 AC 6): on the seeded database, `EXPLAIN` of each of the four
  queries as the repositories issue them shows an index scan on the new index and no `Seq Scan` on that table
  (`SET enable_seqscan` left on; `ANALYZE` first).
- `test_activation_reads_one_account_row` (SR-026 AC 6; PRB-022 regression): count SQL statements touching
  `account` during `validate` with 1 and with 1 000 accounts: equal, and one row fetched.
- Recorded in TS-018 (TC-018.4 indexes, TC-018.5 activation).

## Acceptance criteria

- [ ] SR-026 AC 6: four indexes; plan check shows no sequential scan; activation reads one row.
- [ ] Migration up and down on an empty and a populated database.
- [ ] 0011 not applied to any existing database without the human's go-ahead.

## Definition of Done

- [ ] `ruff`, `mypy`, backend suite (PostgreSQL tests) green
- [ ] TS-018 updated; ADD-016 consistent
- [ ] `traceability-check` no error for this record

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect) for PRB-021 and the PRB-022
  regression guard (D-1).
