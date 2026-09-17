---
id: "TS-003"
type: test-specification
title: "Identity, account creation, activation and lifecycle verification"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links:
  - target: "SR-003"
    relation: verifies
  - target: "SR-004"
    relation: verifies
  - target: "SR-032"
    relation: verifies
  - target: "SR-033"
    relation: verifies
  - target: "SR-034"
    relation: verifies
tags: ["level:unit", "class:B"]
---

# TS-003 — Identity, account creation, activation and lifecycle verification

## Scope

Software requirements covered: SR-003, SR-004, SR-032, SR-033, SR-034.
Software items under test: SI-IDENTITY, SI-WORKER, SI-FE-AUTH, SI-FE-CORE.
Levels: unit, integration.

## Preconditions and environment

Build: branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 20 with `frontend/package-lock.json`.
Unit and service tests run with no external services (in-memory repositories and a fake mailer). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: [ADD-004](../architecture/ADD-004-soup-list.md).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-003.1 | SR-003, SR-004 | `backend/tests/identity/test_account_service.py`, `backend/tests/db/test_constraints.py` *(real DB)* | Email is unique, the profile is readable, and a user type is mandatory | Duplicate email rejected at the database level |
| TC-003.2 | SR-032 | `backend/tests/api/test_accounts_router.py`, `frontend/src/core/admin/accounts/AccountsPage.test.tsx` | Only permitted roles create accounts, and only the roles they may create | Every forbidden combination rejected |
| TC-003.3 | SR-033 | `backend/tests/identity/test_activation.py`, `backend/tests/api/test_activation_router.py`, `frontend/src/auth/ActivationPage.test.tsx` | A single-use token expires after 72 hours; resend works; the UI matches the contract | Reuse and expiry both rejected |
| TC-003.4 | SR-034 | `backend/tests/identity/test_lifecycle.py`, `backend/tests/api/test_lifecycle_router.py`, `backend/tests/workers/test_session_revoke.py` | Deactivation kills sessions within the stated window; deletion requires confirmation and releases the email | Session revocation propagation asserted |
| TC-003.5 | SR-025, SR-033 | `frontend/src/auth/ChangePasswordPage.test.tsx`, `frontend/src/auth/ForcedPasswordGate.test.tsx` | A forced password change cannot be bypassed | Gate asserted against the real `/me` contract |

## Acceptance criteria (class B unit level, §5.5.3)

- Initialization: a newly created account cannot authenticate before activation.
- Fault handling: a failed activation email leaves the account in a resendable state.
- Boundary: token accepted at 71h59m, rejected at 72h01m.

## Notes

TC-003.1 partly depends on real-DB tests, which were blocked in TR-001 (no Docker daemon).
