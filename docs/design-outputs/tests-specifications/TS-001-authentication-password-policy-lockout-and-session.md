---
id: TS-001
type: test-specification
title: Authentication, password policy, lockout and session verification
status: approved
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-06"
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
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon; TC-001.6 likewise needs a Docker daemon for the Redis container.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-001.1 | SR-002 | `backend/tests/auth/test_login_service.py` | Valid credentials return a session; invalid ones return the same generic failure with comparable timing | All cases pass; no message distinguishes unknown user from wrong password |
| TC-001.2 | SR-025 | `backend/tests/auth/test_password_service.py` | Complexity, history and reuse rules enforced server-side | Every rule has a rejecting and an accepting case |
| TC-001.3 | SR-029 | `backend/tests/auth/test_lockout.py`, `backend/tests/api/test_lockout_integration.py` | Account locks after the configured failures and unlocks per policy; the login route uses the service | Lock, reject-while-locked and unlock all covered end to end |
| TC-001.4 | SR-030 | `backend/tests/auth/test_session_service.py`, `backend/tests/auth/test_cookies.py` | Sessions are opaque, expire on idle and absolute limits, are revocable, and cookies are Secure/HttpOnly/SameSite=Strict | Each session attribute asserted explicitly |
| TC-001.5 | SR-030 | `frontend/src/auth/LoginPage.test.tsx`, `frontend/src/auth/IdleWarningDialog.test.tsx`, `frontend/src/auth/useIdleTimer.test.ts`, `frontend/src/auth/RequireAuth.test.tsx` | The UI warns before expiry, extends on request and redirects an unauthenticated user | Warning, extend and redirect paths covered |
| TC-001.6 | SR-030 (AC 7) | `backend/tests/auth/test_session_cap_concurrency.py` (`test_concurrent_logins_keep_exactly_the_cap`, 20 repetitions, real Redis `redis:7.4.12-bookworm` container, 10 simultaneous logins at a cap of 3), `backend/tests/auth/test_session_service.py` (`test_cap_holds_over_many_sequential_logins`, `test_cap_transaction_retries_after_concurrent_write`, `test_cap_transaction_gives_up_after_bounded_attempts`, `test_concurrency_cap_evicts_oldest`) | The cap check, eviction and insertion are one optimistic Redis transaction (WATCH/MULTI/EXEC): concurrent logins leave exactly 3 sessions in the account set and as keys, the three pre-existing (oldest) sessions are evicted, every login at the cap evicts exactly one distinct session, and no evicted session key remains; a write between WATCH and EXEC makes the attempt retry; contention that never clears raises after a bounded number of attempts and stores nothing | All 20 repetitions pass; sequential behaviour unchanged; retry and give-up paths covered |
| TC-001.7 | SR-029 (AC 1), SR-030 (AC 5) | `backend/tests/auth/test_login_service.py` (`test_login_without_lockout_svc_raises_type_error`, `test_login_success_resets_the_lockout_counter`, `test_login_wrong_password_records_the_failure`), `backend/tests/test_config.py` (`test_settings_builds_without_session_signing_key`, `test_stale_session_signing_key_is_ignored`), `mypy app` | The login flow cannot be called without a lockout service (`TypeError` at run time, `call-arg` error from mypy); the app boots without `SESSION_SIGNING_KEY` and ignores a stale one in the environment or `.env` | Omitting `lockout_svc` fails; Settings has no signing-key field and builds with and without a leftover value |

## Acceptance criteria (class B unit level, §5.5.3)

- Each acceptance criterion of SR-002, SR-025, SR-029 and SR-030 maps to at least one case above.
- Boundary conditions covered: exactly-at-threshold failed attempts, session expiry at the idle and absolute limits, password at minimum length.
- Fault handling: a Redis outage surfaces as an error, never as an authenticated session.

## Notes

`SessionActivityProvider` and `api/csrf.ts` have no unit tests (PRB-017, TASK-146); until that closes, the client side of SR-030 is only partly verified.

## Version history

- 1.2 (2026-10-31) — TASK-140 (CR-004): added TC-001.7 (lockout service required, no session signing key). Content changed, so the 1.1 approval no longer applies: status set to `in_review` and the approval record removed for re-approval. TASK-199 adds TC-001.6 under the same version.
- 1.2 (2026-10-31) — QA review (TASK-140): approved (`in_review → approved`). TC-001.6 (TASK-199) not yet added; adding it returns TS-001 to `in_review`.
- 1.3 (2026-11-02) — TASK-199 (CR-004): added TC-001.6 (atomic concurrent-session cap, SR-030 AC 7; PRB-023). Content changed, so the 1.2 approval no longer applies: status set to `in_review` for re-approval (no approval record on the file).
- 1.3 (2026-11-06) — QA review (TASK-199): approved (`in_review → approved`). TC-001.6 run by QA: 100 of 100 repetitions passed; negative control and WATCH mutation fail 20 of 20.
