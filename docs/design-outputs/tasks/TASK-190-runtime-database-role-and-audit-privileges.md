---
id: "TASK-190"
type: task
title: "Runtime database role with no UPDATE or DELETE on the audit table"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-11-01"
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

- [x] SR-023 AC 8: `UPDATE`/`DELETE` (and `TRUNCATE`) on `audit_log` as the runtime role fail with
      a permission error (`backend/tests/db/test_audit_append_only_privileges.py`).
- [x] The application's normal statements work as the runtime role (same file, and the audit
      persistence tests run as that role).
- [x] Migrations 0009 up and down pass (`backend/tests/db/test_migration.py`).

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

- [x] Backend suite and DICOM module tests pass; coverage ≥ 85 %.
- [x] TS-009 and SOUP-020 `in_review`.
- [x] `traceability-check` shows no error for TASK-190, TS-009, SR-023.

## Implementation notes (2026-11-01)

- **Files.** `backend/app/db/roles.py` (new; `apply`, `main`), `backend/app/db/alembic/versions/0009_drop_audit_log_rules.py`
  (new), `backend/tests/db/test_audit_append_only_privileges.py` (new, TC-009.11), and a `runtime_engine`
  fixture in `backend/tests/audit/test_failure_audit_persistence.py`,
  `backend/tests/attachments/test_attachment_integrity_persistence.py` and
  `backend/modules/dicom_viewer/tests/test_failure_audit_persistence.py` (the application engine is the
  runtime role; set-up, read-back and clean-up use the owner connection). TS-009 1.9, SOUP-020 1.3 and the
  PRB-005 interim note are updated.
- **Fixture location.** The task named `tests/db/conftest.py` or a shared module. The DICOM module tests
  live outside `backend/tests` and cannot import a shared test module, so each of the three
  persistence tests defines the same short fixture, and the new test file defines its own container.
- **`DATABASE_OWNER_URL`** stays a process-environment variable (TASK-197's rule); `roles.main()` reads it
  and `DATABASE_URL`. It is not a Settings field. Making it required in the `db-migrate` process is C1,
  TASK-191.
- **Grants.** `apply` grants on all tables of schema `public`, which includes `alembic_version`, as ADR-0017
  words it. `TRUNCATE` is never granted by that statement; the `REVOKE` states it explicitly.
- **`apply` refuses** a runtime user equal to the owner user (a revoke on a superuser would do nothing).
- **Not done here (TASK-191).** The `db-migrate` Compose service, the runtime role in deployment, calling
  `roles.main()` after alembic, `enforce()` before alembic, the entrypoint change (PRB-061), and the rehearsal
  on a populated database. `alembic/env.py` still migrates with `DATABASE_URL`; TASK-191 must point it at
  `DATABASE_OWNER_URL` once the application's URL is the runtime role.
- **Task text correction.** Seven test files delete `audit_log` rows, not three; the other four
  (`test_audit_client_address.py`, `test_audit_no_secrets.py`, `test_authz_decision_audit.py`,
  `dicom_viewer/tests/test_audit_module_key.py`) already use a superuser engine and are unchanged.
- **Verification run.** `uv run pytest tests/db tests/audit tests/attachments` 258 passed; DICOM module
  tests 25 passed; full suite 1074 passed, 4 skipped, coverage 93.78 %; ruff, black, mypy clean; infra tests 55
  OK; alembic upgrade head, downgrade -1, upgrade head and `python -m app.db.roles` on a scratch container.
  Negative controls: `REVOKE` removed (4 cases fail), runtime engine connected as the owner (8 fail), 0009
  made a no-op (7 fail, including the silent `DO INSTEAD NOTHING` behaviour).

## QA review round 1 (QA engineer, 2026-11-01): APPROVED

TASK-190 `in_review → approved`; TS-009 1.9 `in_review → approved`. SOUP-020 1.3 stays `in_review`:
the human approves it. No CRITICAL or HIGH finding. **One human decision is needed before the
commit** (finding 1).

1. **MEDIUM — ordering window between this commit and TASK-191 (human decision).** Demonstrated on
   a scratch `postgres:16` container, connected as the owner/superuser as today's Compose does: at
   0008, `UPDATE audit_log SET action='TAMPERED'` returns rowcount 0 and the row is unchanged; after
   `upgrade head` (0009) the same `UPDATE` changes the row (rowcount 1) and `DELETE` removes it. So,
   on any database migrated with this commit while the application still connects as the owner,
   tampering goes from a silent no-op to permitted until TASK-191 deploys the runtime role. Also
   shown: keeping the rules and adding the `REVOKE` (option c, first form) does not meet AC 8: with
   the rules at 0008, the runtime role's `UPDATE`/`DELETE` return rowcount 0 with no 42501, because
   `DO INSTEAD NOTHING` discards the statement before the privilege check. **Recommendation: (a),
   accept the window**, because A-1 holds (no release, no real installation; the plan-risk table
   says no real installation is migrated in CR-004), A-3 is confirmed (no code path updates or
   deletes audit rows), the rules never stopped the owner (it can drop them), and TASK-191 is the
   next numbered task with Checkpoint C gating it. Conditions, carried to TASK-191: the branch is not
   merged, tagged or deployed to any shared database between the TASK-190 and TASK-191 commits; and
   PRB-005's Resolution in TASK-191 states that 0009 removed the rules before the role was deployed.
   Option (b), moving 0009 into TASK-191, is also sound and closes the window, at the cost of moving
   the 0009 tests. A trigger that raises 42501 for every role would close it too, but it reverses
   ADR-0017's decision and changes the seven test clean-ups. This is a temporary weakening of a
   RISK-006 control, which is a risk-acceptability decision: **the human must confirm (a) or
   choose (b)**. If (b) or the trigger is chosen, this task is reopened.
2. **MEDIUM — `apply` does not converge a pre-existing role** (`backend/app/db/roles.py:37-39`).
   `ALTER ROLE` resets the attributes but leaves memberships and ownership. Probe: a role that
   already existed (SUPERUSER, `GRANT <owner> TO` it, owning a table), after `apply`, is
   `rolsuper=false, rolinherit=false`. But it still `UPDATE`s `audit_log` (rowcount 1), because in
   PostgreSQL 16 the INHERIT option belongs to each grant and `ALTER ROLE ... NOINHERIT` does not
   change it. It can also `SET ROLE <owner>`. `apply` also silently demotes any other superuser named
   as the runtime user. A role that `apply` creates itself has no membership (`pg_auth_members`
   empty), so a fresh install is safe. → After the `CREATE`/`ALTER`, refuse (raise) when the role
   is a member of any role or owns any relation, schema or database. Alternatively revoke the
   memberships. Refuse an existing role that has `rolsuper`. Add tests. Carried to TASK-191: this is
   where an operator-chosen role first meets `apply`.
3. **LOW — `alembic_version` is writable by the runtime role** (`roles.py:47`, ACL
   `medhub_app=arwd`). A compromised runtime credential can restamp the schema and make the next
   `db-migrate` re-run or skip migrations. It already can delete business data, so the gain is
   small. → After the grants, `REVOKE INSERT, UPDATE, DELETE ON public.alembic_version` when
   `to_regclass('public.alembic_version')` is not null. The guard is needed: an unguarded revoke
   breaks the three `create_all` persistence fixtures (my negative control: 8 errors). Carried to
   TASK-191.
4. **LOW — test gaps** (`backend/tests/db/test_audit_append_only_privileges.py`). Nothing asserts
   `SET ROLE <owner>` is refused or that `pg_auth_members` is empty for the runtime role. My
   mutation that adds `GRANT <owner> TO <runtime>` (NOINHERIT kept) passes all 18 tests. `TRUNCATE
   ... CASCADE` from another table is not tested. It is refused today: no FK touches `audit_log`,
   and the role has no TRUNCATE on any table. → Add `SET ROLE <owner>` and `TRUNCATE "group"
   CASCADE` to the refused cases. Assert there are no memberships in
   `test_runtime_role_is_unprivileged_and_owns_nothing`.
5. **LOW — the password is sent as plaintext in DDL** (`roles.py:33-35`). Quoting is safe:
   `sql.Literal`, and a password with quotes, `;`, `--` and a backslash logs in and leaves
   `account` intact. The application never logs it: `main()` prints the user name only. The server,
   however, records the statement under `log_statement=ddl|all`, or in its error log when the
   statement fails. → Send a SCRAM verifier instead:
   `psycopg2.extensions.encrypt_password(password, user, conn, "scram-sha-256")`. Carried to
   TASK-191 (optional hardening).

**Checked, no finding.**
- PostgreSQL 16: `PUBLIC` has no `CREATE` on schema `public` and no `UPDATE`/`DELETE` on
  `audit_log`. `pg_default_acl` is empty. There is no `SECURITY DEFINER` function in `public`, no
  FK to or from `audit_log`, and no trigger on it.
- As the runtime role: `GRANT UPDATE ON audit_log TO` itself is a no-op (the ACL stays
  `medhub_app=ar`). `ALTER ... OWNER`, `DISABLE TRIGGER`, `CREATE FUNCTION`, `CREATE SCHEMA` and
  `SET SESSION AUTHORIZATION` are refused with 42501. `TEMP` tables are allowed (`PUBLIC`
  default): harmless.
- Default privileges are not used: a later table gets its grants only when `apply` is re-run. The
  test proves the refusal before the re-run, and the docstring says "on the next run", which is
  accurate. TASK-191 must keep `alembic upgrade head && python -m app.db.roles` in one `db-migrate`
  run, with no other migrating process.
- The seven files that delete audit rows: the three changed ones run the app on the runtime role
  (`get_engine` patched) and only seed, read back and clean up as the owner. The other four run the
  app as the superuser. They do not exercise AC 8, so no privilege failure is hidden. They do not
  prove their flows' grants under the runtime role either; TASK-191's started stack covers that.
- ADD-016 1.1 already describes `U-PER-Roles` as built; nothing to confirm.

**Pre-existing (not blocking).** The testcontainers fixtures use the floating `postgres:16` tag,
which resolved to 16.14 here, while SOUP-020 pins 16.15. TC-009.11's evidence for SOUP-020's new
relied-on requirement comes from 16.14.

**Verification run (QA, 2026-11-01).** `pytest tests/db tests/audit tests/attachments`: 258 passed.
Full suite with coverage: 1074 passed, 4 skipped, 93.76 %. DICOM module tests: 25 passed. ruff,
black (249 unchanged) and mypy (130 files): clean. Infra unittest: 55 OK. Migrations: 0008 → head
→ 0008 → head on a scratch container (my probe), plus `test_migration.py` and
`test_owner_role_runs_migrations_up_and_down`. Negative controls in scratch copies:
- REVOKE removed: 4 fail (UPDATE/DELETE).
- TRUNCATE granted, with the REVOKE without TRUNCATE: 2 fail.
- 0009 made a no-op: 7 fail.
- Owner membership granted: 0 fail (finding 4).
- Traceability (TASK-190, TS-009, SOUP-020, PRB-005, SR-023): 0 errors, 18 warnings. All are W5/W6
  on records still `in_review` or obsolete.
