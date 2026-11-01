---
id: "PRB-005"
type: problem-report
title: "Audit log is append-only by convention rather than by the database, and its scrub is pattern-limited"
status: open
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-01"
criticality: major
links: []
tags: ["security", "hazard:detectability"]
---

# PRB-005 — Audit log is append-only by convention rather than by the database, and its scrub is pattern-limited

## Observed

`app/audit/service.py` relies on callers never updating or deleting audit rows — no database grant or trigger enforces it — and the credential scrub is a regex/pattern list, so an unexpected field name can carry a secret into the log.

## Impact

SR-023 (audit logging of security-relevant events) can be defeated by any future code path, which undermines the evidence needed to detect a wrong disclosure.

## Investigation

Read on 2026-10-31 (CR-004 Plan stage, Software Architect role). **The report is partly stale:
the database does enforce something, but not what SR-023 AC 8 requires. A second, live gap was
found.**

1. **Append-only.** Migration `backend/app/db/alembic/versions/0006_audit_log_append_only_rules.py:23-25`
   creates two PostgreSQL rules, `ON UPDATE / ON DELETE TO audit_log DO INSTEAD NOTHING`. So
   "no database grant or trigger enforces it" is not accurate. But the rules
   - turn an `UPDATE` or `DELETE` into a silent no-op that reports success, not the permission
     error SR-023 AC 8 requires, so a tampering attempt leaves no trace;
   - can be dropped by the role the application connects with, because that role owns the table.
     The application, the worker and the migrations all connect as `medhub`
     (`infra/.env.example:14`), which is `POSTGRES_USER` of the official image
     (`infra/docker-compose.yml:90-92`) and therefore a **superuser**. Privileges do not apply to
     a superuser, so a `REVOKE` alone would change nothing. The migrations run with the same URL
     (`backend/entrypoint.sh:4`).
   - are not present in most tests: `backend/tests/db/conftest.py:21` builds the schema with
     `create_all`, not with the migrations.
2. **Secret scrub.** `backend/app/audit/service.py:12-24` redacts only `key=value` text whose key
   is `password`, `secret`, `token`, `key` or `credential`. A bare secret in any field passes.
   **Live instance:** `POST /auth/logout` records `target_id=session.session_id`
   (`backend/app/api/routers/auth.py:101-108`). The session id **is** the bearer token
   (`backend/app/auth/session.py:78`, read from the cookie at `backend/app/api/deps.py:55`). The
   session is invalidated just before (`auth.py:98`), so the stored token is dead, but it is a
   credential in plaintext in the audit trail (SR-023 AC 5, AC 9).
3. `audit_log` has no free-text field: only `action`, `target_type`, `target_id`
   (`backend/app/db/models/audit.py:19-34`). `action` and `target_type` are plain `str`
   parameters (`service.py:31-39`); two callers pass literals (`"LOGOUT"`, `"PASSWORD_CHANGED"`,
   `auth.py:103,165`).

**CR-004 A-3 (no code path updates or deletes `audit_log` rows) is confirmed:** the only
references to `AuditLog` or `audit_log` under `backend/app`, `backend/modules` and
`backend/scripts` are the model, the append-only repository (`add`, `add_independent`), the
service and migrations 0001 and 0006. `actor_id` is not a foreign key (`audit.py:22-23`), so no
cascade reaches it, and the erasure flow only inserts events (`backend/app/identity/erasure.py:105-117`).
Three **tests** delete audit rows to clean up (`backend/tests/audit/test_failure_audit_persistence.py:61`,
`backend/tests/attachments/test_attachment_integrity_persistence.py:102`,
`backend/modules/dicom_viewer/tests/test_failure_audit_persistence.py:90`); under the planned
privileges they must clean up with the owner role.

## Safety evaluation

Contributes to RISK-006 (incomplete audit trail). No tampering observed.

## Resolution

Planned in CR-004: TASK-190 (separate runtime and migration roles; `UPDATE`, `DELETE` and
`TRUNCATE` on `audit_log` refused to the runtime role; the silent rules dropped), TASK-191 (the
deployment connects with the runtime role; migrations run once, as the owner, before the
application starts; rehearsed on a copy of a populated database), TASK-192 (typed audit fields,
so no secret can be stored in any field; the logout event no longer stores the session token).
The design is [ADR-0017](../design/adr/0017-database-roles-and-append-only-audit-log.md). Not yet
fixed.

**Interim (TASK-192, 2026-10-31): scrub part done.** `AuditService.record` now refuses any `action`, `target_type` or `target_id` outside closed shapes (`AuditFieldError`), and logout records the account id, not the session token (`backend/tests/audit/test_audit_no_secrets.py`, TS-009 TC-009.12). Still open: the append-only part, TASK-190 and TASK-191 (DB-enforced through role privileges). The report moves to `resolved` with TASK-191, the last PRB-005 task.

**Interim (TASK-190, 2026-11-01): database side done.** Migration 0009 drops the `DO INSTEAD NOTHING` rules of 0006, and `app.db.roles.apply` creates the runtime role with no `UPDATE`, `DELETE` or `TRUNCATE` on `audit_log`; as that role the statements fail with SQLSTATE 42501 (`backend/tests/db/test_audit_append_only_privileges.py`, TS-009 TC-009.11). The deployment still connects as the owner role and does not run `app.db.roles`, so the defect is not fixed in a running system until TASK-191. The report stays `open`.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Medium.

## Version history

- 1.3 (2026-11-01) — TASK-190: interim Resolution note (database side done; deployment open with TASK-191). Status unchanged.
- 1.2 (2026-10-31) — TASK-192: interim Resolution note (scrub part done; append-only part open with TASK-190 and TASK-191). Status unchanged.
- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
