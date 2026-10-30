---
id: TS-001
type: test-specification
title: Authentication, password policy, lockout and session verification
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-30"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-30"
approved_digest: 8676a99a6ba10cb4f58e55d63f126b2c5059302a67d38b064cf56f3489c2d172
approval_note: self-approved
links:
  - target: SR-002
    relation: verifies
  - target: SR-025
    relation: verifies
  - target: SR-029
    relation: verifies
  - target: SR-030
    relation: verifies
tags:
  - level:unit
  - class:B
---

# TS-001 — Authentication, password policy, lockout and session verification

## Scope

Software requirements covered: SR-002, SR-025, SR-029, SR-030.
Software items under test: SI-AUTH, SI-FE-AUTH.
Levels: unit, integration.

## Preconditions and environment

Build: branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 24 LTS (build stage node:24.22.2-trixie-slim; CI node-version 24) with `frontend/package-lock.json`.
Unit and service tests run with no external services (fakeredis substitutes Redis; no network). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-001.1 | SR-002 | `backend/tests/auth/test_login_service.py` | Valid credentials return a session; invalid ones return the same generic failure with comparable timing | All cases pass; no message distinguishes unknown user from wrong password |
| TC-001.2 | SR-025 | `backend/tests/auth/test_password_service.py` | Complexity, history and reuse rules enforced server-side | Every rule has a rejecting and an accepting case |
| TC-001.3 | SR-029 | `backend/tests/auth/test_lockout.py`, `backend/tests/api/test_lockout_integration.py` | Account locks after the configured failures and unlocks per policy; the login route uses the service | Lock, reject-while-locked and unlock all covered end to end |
| TC-001.4 | SR-030 | `backend/tests/auth/test_session_service.py`, `backend/tests/auth/test_cookies.py` | Sessions are opaque, expire on idle and absolute limits, are revocable, and cookies are Secure/HttpOnly/SameSite=Strict | Each session attribute asserted explicitly |
| TC-001.5 | SR-030 | `frontend/src/auth/LoginPage.test.tsx`, `frontend/src/auth/IdleWarningDialog.test.tsx`, `frontend/src/auth/useIdleTimer.test.ts`, `frontend/src/auth/RequireAuth.test.tsx` | The UI warns before expiry, extends on request and redirects an unauthenticated user | Warning, extend and redirect paths covered |

## Acceptance criteria (class B unit level, §5.5.3)

- Each acceptance criterion of SR-002, SR-025, SR-029 and SR-030 maps to at least one case above.
- Boundary conditions covered: exactly-at-threshold failed attempts, session expiry at the idle and absolute limits, password at minimum length.
- Fault handling: a Redis outage surfaces as an error, never as an authenticated session.

## Notes

`SessionActivityProvider` and `api/csrf.ts` have no unit tests (PRB-017, TASK-146); until that closes, the client side of SR-030 is only partly verified.
