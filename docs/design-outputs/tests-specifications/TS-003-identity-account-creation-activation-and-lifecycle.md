---
id: TS-003
type: test-specification
title: Identity, account creation, activation and lifecycle verification
status: approved
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-31"
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
| TC-003.3 | SR-033 | `backend/tests/identity/test_activation.py`, `backend/tests/api/test_activation_router.py`, `frontend/src/auth/ActivationPage.test.tsx` | A single-use token expires after 72 hours; resend works; the UI matches the contract | Reuse and expiry both rejected |
| TC-003.4 | SR-034 | `backend/tests/identity/test_lifecycle.py`, `backend/tests/api/test_lifecycle_router.py`, `backend/tests/workers/test_session_revoke.py` | Deactivation kills sessions within the stated window; deletion requires confirmation and releases the email | Session revocation propagation asserted |
| TC-003.5 | SR-025, SR-033 | `frontend/src/auth/ChangePasswordPage.test.tsx`, `frontend/src/auth/ForcedPasswordGate.test.tsx` | A forced password change cannot be bypassed | Gate asserted against the real `/me` contract |
| TC-003.6 | SR-032 AC 1, AC 4, AC 5; SR-034 AC 1 | `backend/tests/authz/test_decision_table.py` (identity tables: `test_create_by_role_and_target`, `test_create_denied_for_actor_with_no_known_role`, `test_deactivate_by_role_and_relation`, `test_reactivate_by_role_and_relation`, `test_lifecycle_refusal_precedes_the_lookup`, `test_lifecycle_denied_for_actor_with_no_known_role`, `test_delete_by_role_and_relation`, `test_delete_denied_for_actor_with_no_known_role`, `test_resend_activation_by_role`, `test_resend_activation_denied_for_actor_with_no_known_role`), `backend/tests/identity/` | Account creation (creator role x target type), deactivate, reactivate, delete (actor role x self/other) and activation resend are decided in `AuthorizationService`; the table written against the old role comparisons stays green after the move, with every status code and `detail` message unchanged | 55 identity table cases pass before and after the move; the table fails if a moved rule is weakened |

## Acceptance criteria (class B unit level, §5.5.3)

- Initialization: a newly created account cannot authenticate before activation.
- Fault handling: a failed activation email leaves the account in a resendable state.
- Boundary: token accepted at 71h59m, rejected at 72h01m.

## Notes

TC-003.1 partly depends on real-DB tests, which were blocked in TR-001 (no Docker daemon).

## Version history

- 1.2 (2026-10-31) — TASK-188: TC-003.6 added (identity and lifecycle access rules decided centrally, table unchanged, SR-032 AC 1/4/5, SR-034 AC 1). Approval record cleared; returned to `in_review`.
- 1.2 (2026-10-31) — QA review (TASK-188): approved (`in_review → approved`).
