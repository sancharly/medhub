---
id: "PRB-005"
type: problem-report
title: "Audit log is append-only by convention rather than by the database, and its scrub is pattern-limited"
status: resolved
version: "1.5"
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

Fixed in CR-004 by three tasks (design: [ADR-0017](../design/adr/0017-database-roles-and-append-only-audit-log.md)).

- **TASK-192 (scrub).** `AuditService.record` refuses any `action`, `target_type` or `target_id`
  outside closed shapes (`AuditFieldError`); logout records the account id, not the session token
  (`backend/tests/audit/test_audit_no_secrets.py`, TS-009 TC-009.12).
- **TASK-190 (database).** Migration 0009 drops the `DO INSTEAD NOTHING` rules of 0006, and
  `app.db.roles.apply` creates the runtime role with no `UPDATE`, `DELETE` or `TRUNCATE` on
  `audit_log` (`backend/tests/db/test_audit_append_only_privileges.py`, TS-009 TC-009.11).
  **Migration 0009 removed the rules before the runtime role was deployed**: between TASK-190
  (commit `b5294d8`) and TASK-191 an owner-connected `UPDATE` or `DELETE` on `audit_log` succeeded.
  The human accepted that window (CR-004 D-4, 2026-11-01); the branch was not merged, tagged or
  deployed to a shared database in it.
- **TASK-191 (deployment).** The one-shot `db-migrate` service runs, as the owner, the secret
  check, `alembic upgrade head` and `python -m app.db.roles`; `backend`, `celery-worker` and
  `celery-beat` connect as the runtime role `medhub_app` and start only after it exits 0. The role
  also cannot write `alembic_version`, cannot `SET ROLE` to another role and has no membership;
  `roles.apply` refuses a pre-existing role that is a superuser, a member of a role or an owner
  of objects, resets `REPLICATION` and `BYPASSRLS`, and leaves only `SELECT` and `INSERT` on
  `audit_log`.
- **TASK-191 round 2 (QA finding 1, HIGH).** The first version of the deployment still passed the
  owner (superuser) password to the application services through `env_file: .env`
  (`POSTGRES_PASSWORD`), so a compromised application process could reconnect as the owner and
  alter `audit_log`. Fixed: no service reads `env_file`; each lists only the settings it reads, and
  the owner password and `DATABASE_OWNER_URL` reach `postgres` and `db-migrate` only. The defect is
  closed only with this fix: it is verified by value on a started stack (smoke test section 12;
  `infra/tests/test_compose_db_roles.py`).

Verification, reproducible:

1. `cd backend && uv run pytest tests/db/test_audit_append_only_privileges.py tests/core/test_secret_settings.py`
   (real PostgreSQL 16 via testcontainers): `UPDATE`, `DELETE` and `TRUNCATE` on `audit_log`,
   `TRUNCATE "group" CASCADE`, `SET ROLE <owner>`, `DROP`/`ALTER` of the table and writes to
   `alembic_version` all fail with 42501; `pg_auth_members` holds no row for the role.
2. `cd infra && python3 -m unittest discover -s tests` (`test_compose_db_roles.py`): `db-migrate`
   is one-shot, only it has `DATABASE_OWNER_URL`, the application services wait for its success.
3. Started stack, scratch Compose project (copy of the tree, own `.env`):
   `docker compose -p <project> up -d --build && COMPOSE_PROJECT_NAME=<project> bash infra/smoke-test.sh`
   passes 64 checks, among them "runtime role: update/delete/truncate on audit_log fails with
   42501" and "backend is connected as the runtime role". With `DATABASE_URL` pointed at the owner,
   five of them fail (negative control).
4. Rehearsal on a populated database (TASK-191 `## Implementation notes`, TS-009 TC-009.11): the
   previous release at migration 0008 with the rules in place and 5015 `audit_log` rows was
   upgraded; counts and a checksum of the 5015 rows were unchanged; as `medhub_app`, `UPDATE`,
   `DELETE` and `TRUNCATE` failed with 42501 and the 5000 seeded rows remained.

The owner role can still alter `audit_log`; its credential is held only by the `postgres` and
one-shot `db-migrate` containers, and no application process has it (checked by value, see above).
A superuser of the database host is outside this report.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Medium.

## Version history

- 1.3 (2026-11-01) — TASK-190: interim Resolution note (database side done; deployment open with TASK-191). Status unchanged.
- 1.2 (2026-10-31) — TASK-192: interim Resolution note (scrub part done; append-only part open with TASK-190 and TASK-191). Status unchanged.
- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
- 1.4 (2026-11-01) — TASK-191: final Resolution (deployment connects as the runtime role; started-stack and rehearsal evidence); migration 0009 removed the rules before the role was deployed (window accepted, CR-004 D-4). Status `open` → `resolved`.
- 1.5 (2026-11-01) — TASK-191 round 2: the owner password no longer reaches the application services (QA finding 1); Resolution names the fix and the by-value verification. Remains `resolved`.
