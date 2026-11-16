---
id: "TASK-219"
type: task
title: "Indexes for the four authorization lookups (migration 0011) and the one-row activation guard"
status: approved
version: "1.1"
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

- [x] SR-026 AC 6: four indexes; plan check shows no sequential scan; activation reads one row.
- [x] Migration up and down on an empty and a populated database.
- [x] 0011 not applied to any existing database without the human's go-ahead.

## Definition of Done

- [x] `ruff`, `mypy`, backend suite (PostgreSQL tests) green
- [x] TS-018 updated; ADD-016 consistent
- [x] `traceability-check` no error for this record

## Implementation record (2026-11-13, Software Developer)

- Models: `Index(...)` added to `Appointment`, `ConsentGrant`, `ClinicalEntry`, `Attachment`
  (`__table_args__`). Migration `0011_authorization_lookup_indexes.py`: four `op.create_index`; downgrade
  drops them. Not applied to any existing database; only to testcontainers PostgreSQL.
- Tests: `backend/tests/db/test_migration_0011_indexes.py` (TC-018.5: up/down empty and 10 000 rows per
  table with row counts unchanged; `EXPLAIN` after `ANALYZE`, `enable_seqscan` on, names the new index and
  has no `Seq Scan`; negative control at 0010 shows `Seq Scan`), `backend/tests/identity/test_activation_one_row.py`
  (TC-018.6: 1 and 1 001 accounts, same statement count, one row fetched; negative control with a `list()`
  scan fails `1001 == 1`). The existing `tests/db/test_migration.py` drift check passes.
- Note: no repository issues a query by `appointment.scheduled_at`, by `consent_grant.appointment_id` or
  by `attachment.patient_id` yet (only `ClinicalRepository.list_for_patient` filters by patient); the plan
  check uses the equivalent `select()` on the model. The lookup is `ActivationService.activate`
  (there is no `validate`).
- ADD-016 (approved) already states 0011 as planned; left unchanged.

## QA review round 1 (qa-engineer, 2026-11-13) — APPROVED

Run by QA: `uv run pytest -q` 1645 passed, 10 skipped, 0 failed; the three new tests and `tests/db/test_migration.py`
6 passed; `uv run pytest modules/dicom_viewer/tests` 31 passed; `ruff check .` clean; `ruff format --check` on the
7 changed files clean; `mypy app` clean (135 files); `python3 -m unittest discover -s infra/tests` 178 OK;
traceability (fallback parser) on TASK-219, TS-018, SR-026, SR-033, PRB-021, PRB-022, RISK-007 with one hop:
0 errors, only W5 (approved records linking to the `in_review` RISK-007, RISK-006, SR-023, SR-012 of CR-006).

QA probes: the revision chain is linear (`0011` revises `0010`, the previous head); at 0010 `compare_metadata`
reports exactly the four `add_index` diffs, so the drift test does catch a missing index; at 0010 all four
lookups of the test plan as `Seq Scan` (the shipped negative control checks only `clinical_entry`), and after 0011
they use the new index (bitmap scans for the two patient lookups). The local `infra-postgres-1` is still at 0010
(AC 3). The activation test reads one row with 1 001 accounts through `AccountRepository.get_by_id` (primary key).

Findings:

1. **MEDIUM — the indexes follow SR-026 AC 6 / PRB-021, not the lookups the code issues.** No code queries
   `appointment.scheduled_at`, `consent_grant.appointment_id` or `attachment.patient_id`; only
   `ClinicalRepository.list_for_patient(_ordered)` uses one of the four. The real authorization decision
   (`ConsentRepository.list_active_for_patient_doctor`) was already served by
   `ix_consent_grant_patient_doctor_active`. Two lookups the code does issue still scan after 0011 (QA `EXPLAIN`
   on the 10 000-row seed): `AttachmentRepository.list_for_clinical_entry` (`attachment.clinical_entry_id`,
   `app/attachments/service.py:332`) and `ConsentRepository.list_patients_for_doctor` (`consent_grant.doctor_id`
   and `active`; the composite index leads with `patient_id`; `app/clinical/service.py:106`). PRB-021's claim
   that the four columns are "read on every authorization decision" is wrong for three of them. The task meets the
   approved SR, so this does not block it. → Architect: correct PRB-021's Observed text when it is resolved, and
   raise a PRB (or add to CR-006) for indexes on `attachment.clinical_entry_id` and `consent_grant(doctor_id,
   active)`, or record why they are not needed.
2. **LOW — TASK text and implementation differ.** The Tests section names TC-018.4/TC-018.5 (TS-018 uses
   TC-018.5/TC-018.6, because TC-018.4 already exists) and `validate` (the code has `ActivationService.activate`).
   It also says "as the repositories issue them", but there is no repository query for three of the four
   (finding 1). The implementation record explains the deviations. → Next editor of this record: align the text.
3. **LOW — test comment says something that is not there.** `backend/tests/db/test_migration_0011_indexes.py:171`
   says "as ClinicalRepository.list_for_patient and the attachment lookup by patient issue them". No attachment
   lookup by patient exists. → Reword to "equivalent select() on the model" when the file is next touched.
4. **LOW — negative control covers one of four.** `test_without_the_indexes_the_same_lookups_scan` checks only
   `clinical_entry` (QA confirmed that the other three also scan at 0010). → Loop over the same `queries` dict.
5. **LOW — ADD-016 still says "CR-006 (planned)" for 0011.** ADD-016 1.1 says the implementing tasks confirm the
   unit text when they land, but TASK-225's scope names arc42 07 and DEPLOY.md, not ADD-016. → Add the ADD-016
   "planned" marker to TASK-225, or confirm it in ADD-016 in the CR-006 close-out.
6. **LOW — no version-history entry for the Build stage** (the record stayed 1.0 when it went to `in_review`).
   Recorded together with this review as 1.1.

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect) for PRB-021 and the PRB-022
  regression guard (D-1).
- 1.1 (2026-11-13) — Build stage (Software Developer): implementation record, `draft → in_review`. QA review round 1: APPROVED (1 MEDIUM, 5 LOW; see "QA review round 1"); checkboxes ticked; `in_review → approved`.
