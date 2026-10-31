---
id: "TASK-190"
type: task
title: "Runtime database role with no UPDATE or DELETE on the audit table"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
links:
  - target: "SR-023"
    relation: implements
  - target: "RISK-006"
    relation: mitigates
  - target: "RISK-001"
    relation: mitigates
  - target: "PRB-005"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "ADD-016"
    relation: relates_to
  - target: "ADD-013"
    relation: relates_to
tags: ["security", "audit", "persistence", "cr:CR-004", "control:design"]
---

# TASK-190 — Runtime database role with no UPDATE or DELETE on the audit table

- **Software item / unit:** SI-PERSIST `U-PER-Roles` (new), `U-PER-Migrations` (ADD-016); SI-AUDIT (ADD-013).
- **PRB:** PRB-005 (append-only part). **CR:** CR-004.
- **Depends on:** none in code. **Gate** for TASK-191 (deployment wiring) and TASK-194 (migration 0010
  is numbered after 0009).
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (new `backend/app/db/roles.py`, migration `0009_drop_audit_log_rules.py`, test fixture,
  1 new test file, 3 test clean-ups; TS-009)
- **Needs:** a Docker daemon (testcontainers PostgreSQL).
- **Design:** [ADR-0017](../../design/adr/0017-database-roles-and-append-only-audit-log.md)

## Objective

SR-023 AC 8: an `UPDATE` or `DELETE` on `audit_log` issued with the application's role fails with a
permission error. This task builds and tests the mechanism against a real database; TASK-191 makes
the deployment use it. CR-004 A-3 is confirmed (PRB-005 Investigation): no application code path
updates or deletes audit rows.

## Implementation detail

1. `backend/app/db/roles.py` — `apply(owner_engine, runtime_user, runtime_password)`, idempotent:
   create the role if missing (`LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT`), set its
   password, `GRANT CONNECT` on the database, `USAGE` on schema `public`,
   `SELECT, INSERT, UPDATE, DELETE` on all tables and `USAGE, SELECT` on all sequences, then
   `REVOKE UPDATE, DELETE, TRUNCATE ON audit_log`. Identifiers quoted with `psycopg2.sql`; the
   password never logged. A `main()` reads `DATABASE_OWNER_URL` and `DATABASE_URL` (runtime user
   and password parsed from it).
2. Migration `0009`: drop `no_update_audit_log` and `no_delete_audit_log` (0006). Downgrade
   recreates them.
3. Test fixture (`backend/tests/db/conftest.py` or a shared `tests/conftest_db_roles.py`): after
   `create_all`/migrations as the container superuser, run `roles.apply` and expose a
   `runtime_engine` connected as the runtime role.
4. Test clean-ups that delete audit rows use the owner engine:
   `backend/tests/audit/test_failure_audit_persistence.py:61`,
   `backend/tests/attachments/test_attachment_integrity_persistence.py:102`,
   `backend/modules/dicom_viewer/tests/test_failure_audit_persistence.py:90`.

## Tests (write first)

- `backend/tests/db/test_audit_append_only_privileges.py` (real database, migrations to head,
  `roles.apply`):
  - as the runtime role: `INSERT` into `audit_log` succeeds; `UPDATE`, `DELETE` and `TRUNCATE`
    raise `psycopg2.errors.InsufficientPrivilege` (SQLSTATE 42501);
  - as the runtime role: insert, update and delete on a business table (`group`) succeed;
  - the runtime role is not a superuser and owns no table (`pg_roles`, `pg_tables`);
  - `roles.apply` twice is a no-op; after a new table is created, `apply` grants it;
  - the 0006 rules are gone after upgrade (`pg_rules`).
- `backend/tests/db/test_migration.py`: upgrade and downgrade still pass with 0009.
- `backend/tests/audit/test_failure_audit_persistence.py`: run its requests through an app whose
  engine is the runtime role (the independent audit transaction inserts only).

## Acceptance criteria

- [ ] SR-023 AC 8: `UPDATE`/`DELETE` (and `TRUNCATE`) on `audit_log` as the runtime role fail with
      a permission error (`backend/tests/db/test_audit_append_only_privileges.py`).
- [ ] The application's normal statements work as the runtime role (same file, and the audit
      persistence tests run as that role).
- [ ] Migrations 0009 up and down pass (`backend/tests/db/test_migration.py`).

## Verification

```sh
cd backend && uv run pytest tests/db tests/audit tests/attachments -v
cd backend && uv run pytest modules/dicom_viewer/tests -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
```

Negative control: remove the `REVOKE`; the 42501 cases fail.

## Records

- **TS-009**: TC-009.11 (privilege test, real database), `verifies` SR-023.
- **SOUP-020** (PostgreSQL): add to "Functional and performance requirements" that MedHub relies
  on table privileges being enforced for a non-superuser, non-owner role; `in_review`.
- **ADD-016** 1.1: confirm `U-PER-Roles`.

## Definition of Done

- [ ] Backend suite and DICOM module tests pass; coverage ≥ 85 %.
- [ ] TS-009 and SOUP-020 `in_review`.
- [ ] `traceability-check` shows no error for TASK-190, TS-009, SR-023.
