---
id: "TASK-011"
type: task
title: "Alembic + initial migration + constraints"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-003"
    relation: implements
  - target: "SR-032"
    relation: implements
  - target: "SR-010"
    relation: implements
  - target: "TASK-010"
    relation: relates_to
tags: ["audit-verified", "phase:1-persistence-audit"]
---

- **Phase:** 1 — Persistence & audit
- **Software item / unit:** SI-PERSIST / U-PER-Migrations
- **Implements:** SR-003, SR-032, SR-010
- **Depends on:** TASK-010 (must be merged first)
- **Branch:** `feature/persist-migrations`
- **Status:** Completed (audit-verified 2026-06-29)

## Objective

Configure Alembic and author the initial migration that creates the schema from the TASK-010 models, with the database-level integrity constraints that enforce key requirements at the data layer: unique email across all account states (SR-003.1, SR-032.3), foreign keys for entity references, and CHECK constraints for required appointment fields/enums (SR-010.2). Per SR-032.3 and SR-031, these constraints are a defense-in-depth backstop to application validation, not a replacement for it.

## Interfaces to honor

- Owns the schema lifecycle for `SI-PERSIST`; the migration is the version-controlled source of truth for the DB structure (NFR-006). Only SI-PERSIST manages PostgreSQL schema (rule 12.3.3).
- Must keep migrations consistent with the ORM models (autogenerate-then-review); must **not** add new columns/tables not present in TASK-010 models, and must **not** implement repository/query logic or application validation here.

## Implementation detail

- Files to create / modify:
  - `backend/app/db/alembic/env.py` — wire Alembic to `Base.metadata` (TASK-010) and read `database_url` from `Settings` (TASK-003); offline + online modes.
  - `backend/alembic.ini` — script location, naming convention for constraints (deterministic constraint names for reviewable diffs).
  - `backend/app/db/alembic/versions/0001_initial.py` — initial migration creating all tables with:
    - **UNIQUE** constraint on `account.email` covering all `status` values (INACTIVE/ACTIVE/DEACTIVATED/DELETED) — duplicate email rejected at DB even after deletion (SR-003.1, SR-032.3).
    - **FOREIGN KEYS**: `appointment.doctor_id`/`patient_id` → `account.id`; `clinical_entry.patient_id`/`author_doctor_id` → `account.id`; `attachment.clinical_entry_id` → `clinical_entry.id`, `attachment.patient_id` → `account.id`; `consent_grant.patient_id`/`doctor_id` → `account.id`; `group_membership` / `group_module_enablement` composite FKs (SR-010.1 valid references).
    - **NOT NULL** on `account.user_type`, `account.email`, `account.status` (SR-004); on `appointment.doctor_id`, `appointment.patient_id`, `appointment.scheduled_at` (SR-010.2 reject missing doctor/patient/date-time).
    - **CHECK / Enum types**: PostgreSQL enum types (or CHECK) for `user_type`, `account.status`, `appointment.state`, `consent_grant` source-type, `audit_log.outcome`, `group_membership.source`.
    - **Indexes** for FK columns and frequent lookups (e.g. `account.email`, `consent_grant(patient_id, doctor_id, active)`), supporting §8.9 indexed authorization queries.
  - `infra` note: migration run step added to bring-up/deploy docs (TASK-004 stack runs `alembic upgrade head` on backend start).
- Libraries (exact stack): Alembic, SQLAlchemy 2.x, PostgreSQL 16.
- Config keys: `database_url` from `Settings`.
- Error cases: duplicate email → DB unique violation (surfaced as `409 /errors/conflict` by the API layer later, SR-032.3); missing FK target → integrity error.

## Tests (write first — TDD, CLAUDE.md §4)

- `backend/tests/db/test_migration.py` (ephemeral PostgreSQL):
  - `alembic upgrade head` then `downgrade base` runs cleanly (reversible migration).
  - After upgrade, the schema matches the models (no pending autogenerate diff) — guards model/migration drift.
- `backend/tests/db/test_constraints.py`:
  - **SR-003.1 / SR-032.3**: inserting a second account with an existing email raises a unique-violation, including when the first account's `status` is DELETED.
  - **SR-010.2**: inserting an appointment with NULL `doctor_id`, `patient_id`, or `scheduled_at` is rejected by NOT NULL.
  - **SR-010.1**: an appointment referencing a non-existent doctor/patient id is rejected by the FK.
  - Enum/CHECK columns reject out-of-set values.
- Each test references its SR criterion.

## Acceptance criteria

Distilled from SR-003, SR-032, SR-010:

- [x] A single initial migration creates the full schema and is reversible (`upgrade`/`downgrade`).
- [x] Migration and ORM models are in sync (no pending autogenerate diff).
- [x] `account.email` is unique across all account states; duplicate rejected at the DB even for deleted accounts (SR-003.1, SR-032.3).
- [x] Foreign keys enforce valid doctor/patient/entry references (SR-010.1).
- [x] NOT NULL/CHECK constraints reject appointments missing doctor, patient, or date/time (SR-010.2).
- [x] Enum-constrained columns reject out-of-set values (SR-004 user_type, statuses, states).
- [x] Constraint names are deterministic; migration is version-controlled (NFR-006).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit/integration tests pass against ephemeral PostgreSQL; coverage target met
- [x] OpenAPI regenerated and re-linted (N/A)
- [x] Audit events emitted for security-relevant actions (N/A — schema)
- [x] Traceability matrix row updated (SR-003, SR-032, SR-010 → TASK-011 → constraint/migration tests)
- [x] Security review completed (N/A — no auth/session code)

## Audit verdict (2026-06-29)

- **Verdict:** PASS
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- Acceptance criteria verified met; boxes checked.
