---
id: TS-003
type: test-specification
title: Identity, account creation, activation and lifecycle verification
status: approved
version: "1.6"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-07"
links:
  - target: SR-003
    relation: verifies
  - target: SR-004
    relation: verifies
  - target: SR-032
    relation: verifies
  - target: SR-033
    relation: verifies
  - target: SR-034
    relation: verifies
tags:
  - level:unit
  - class:B
---

# TS-003 — Identity, account creation, activation and lifecycle verification

## Scope

Software requirements covered: SR-003, SR-004, SR-032, SR-033, SR-034.
Software items under test: SI-IDENTITY, SI-WORKER, SI-FE-AUTH, SI-FE-CORE.
Levels: unit, integration.

## Preconditions and environment

Build: branch `fix/review-2026-07-security`, the commit that carries TASK-188 (TC-003.6); TC-003.1 to TC-003.5 last verified on branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 24 LTS (build stage node:24.22.2-trixie-slim; CI node-version 24) with `frontend/package-lock.json`.
Unit and service tests run with no external services (in-memory repositories and a fake mailer). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-003.1 | SR-003, SR-004 | `backend/tests/identity/test_account_service.py`, `backend/tests/db/test_constraints.py` *(real DB)* | Email is unique, the profile is readable, and a user type is mandatory | Duplicate email rejected at the database level |
| TC-003.2 | SR-032 | `backend/tests/api/test_accounts_router.py`, `frontend/src/core/admin/accounts/AccountsPage.test.tsx` | Only permitted roles create accounts, and only the roles they may create | Every forbidden combination rejected |
| TC-003.3 | SR-033 | `backend/tests/identity/test_activation.py`, `backend/tests/api/test_activation_router.py`, `frontend/src/auth/ActivationPage.test.tsx` | A single-use token expires after 72 hours; resend works; the UI matches the contract | Reuse and expiry both rejected; the e-mailed link is `{PUBLIC_BASE_URL}/activation/<token>`, the route the app serves, and the two definitions cannot diverge (`backend/tests/workers/test_email_tasks.py::test_activation_email_link_uses_the_activation_route`, `infra/tests/test_activation_link_route.py`, `frontend/src/core/nav/routeRoles.test.ts`); `backend/tests/workers/test_api_celery_broker.py` (the API lifespan sets the configured Celery app as default: activation e-mail, session-kill, erasure-code and appointment tasks see the Redis broker from a worker thread, PRB-071); on a started stack with no override a real e-mailed link renders the activation page, validates and activates a new account, and a deactivation reaches the worker |
| TC-003.4 | SR-034 | `backend/tests/identity/test_lifecycle.py`, `backend/tests/api/test_lifecycle_router.py`, `backend/tests/workers/test_session_revoke.py` | Deactivation kills sessions within the stated window; deletion requires confirmation and releases the email | Session revocation propagation asserted |
| TC-003.5 | SR-025, SR-033 | `frontend/src/auth/ChangePasswordPage.test.tsx`, `frontend/src/auth/ForcedPasswordGate.test.tsx` | A forced password change cannot be bypassed | Gate asserted against the real `/me` contract |
| TC-003.6 | SR-032 AC 1, AC 4, AC 5; SR-034 AC 1 | `backend/tests/authz/test_decision_table.py` (identity tables: `test_create_by_role_and_target`, `test_create_denied_for_actor_with_no_known_role`, `test_deactivate_by_role_and_relation`, `test_reactivate_by_role_and_relation`, `test_lifecycle_refusal_precedes_the_lookup`, `test_lifecycle_denied_for_actor_with_no_known_role`, `test_delete_by_role_and_relation`, `test_delete_denied_for_actor_with_no_known_role`, `test_resend_activation_by_role`, `test_resend_activation_denied_for_actor_with_no_known_role`), `backend/tests/identity/` | Account creation (creator role x target type), deactivate, reactivate, delete (actor role x self/other) and activation resend are decided in `AuthorizationService`; the table written against the old role comparisons stays green after the move, with every status code and `detail` message unchanged | 67 identity table cases pass before and after the move; the table fails if a moved rule is weakened |
| TC-003.7 | SR-033 AC 7; SR-034 AC 2 | `backend/tests/workers/test_celery_results.py` (`test_task_ignore_result_is_set`, `test_no_code_reads_a_task_result`, `test_enqueue_with_unreachable_redis_fails_fast`); `backend/tests/identity/test_lifecycle.py::test_deactivate_logs_a_warning_when_enqueue_fails` | Dispatching a task never waits on a result store: `task_ignore_result` is set, no code reads a task result, and `.delay()` with Redis unreachable ends within 5 s (19.88 s without the setting); a failed session-kill enqueue is logged with the account id and the deactivation still succeeds | Removing `task_ignore_result` fails the setting test and the fast-fail test; replacing the warning with `pass` fails the warning test |

## Acceptance criteria (class B unit level, §5.5.3)

- Initialization: a newly created account cannot authenticate before activation.
- Fault handling: a failed activation email leaves the account in a resendable state.
- Boundary: token accepted at 71h59m, rejected at 72h01m.

## Notes

TC-003.1 partly depends on real-DB tests, which were blocked in TR-001 (no Docker daemon).

## Version history

- 1.2 (2026-10-31) — TASK-188: TC-003.6 added (identity and lifecycle access rules decided centrally, table unchanged, SR-032 AC 1/4/5, SR-034 AC 1). Approval record cleared; returned to `in_review`.
- 1.2 (2026-10-31) — QA review (TASK-188): approved (`in_review → approved`).
- 1.3 (2026-10-31) — TASK-189 (TASK-188 QA findings 1, 2): TC-003.6 table extended (SYSADMIN target rows for deactivate and delete; no role creates without a requested type, SYSADMIN included). Returned to `in_review`.
- 1.3 (2026-10-31) — QA review (TASK-189 round 2): approved (`in_review → approved`).
- 1.4 (2026-11-07) — CR-004 (TASK-206, PRB-070): TC-003.3 adds the activation link-route tests. Approval cleared, `in_review`.
- 1.5 (2026-11-07) — TASK-206 (PRB-071): TC-003.3 adds the API task-dispatch test and the started-stack e-mail and deactivation checks. `in_review`.
- 1.5 (2026-11-07) — QA review of TASK-206: `approved` (status only; content unchanged).
- 1.6 (2026-11-07) — TASK-207 (TASK-206 QA finding 1, PRB-013 call site): TC-003.7 added (dispatch does not wait on a result store; a failed session-kill enqueue is logged). Approval cleared, `in_review`.
- 1.6 (2026-11-08) — QA review of TASK-207 and TASK-206 re-approval: `approved` (status only; content unchanged).
