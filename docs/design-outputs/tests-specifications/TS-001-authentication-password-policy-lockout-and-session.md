---
id: TS-001
type: test-specification
title: Authentication, password policy, lockout and session verification
status: approved
version: "1.6"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-14"
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
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon; TC-001.6, TC-001.8 and TC-001.9 likewise need a Docker daemon for the Redis container.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-001.1 | SR-002 | `backend/tests/auth/test_login_service.py` | Valid credentials return a session; invalid ones return the same generic failure with comparable timing | All cases pass; no message distinguishes unknown user from wrong password |
| TC-001.2 | SR-025 | `backend/tests/auth/test_password_service.py` | Complexity, history and reuse rules enforced server-side | Every rule has a rejecting and an accepting case |
| TC-001.3 | SR-029 | `backend/tests/auth/test_lockout.py`, `backend/tests/api/test_lockout_integration.py` | Account locks after the configured failures and unlocks per policy; the login route uses the service | Lock, reject-while-locked and unlock all covered end to end |
| TC-001.4 | SR-030 | `backend/tests/auth/test_session_service.py`, `backend/tests/auth/test_cookies.py` | Sessions are opaque, expire on idle and absolute limits, are revocable, and cookies are Secure/HttpOnly/SameSite=Strict | Each session attribute asserted explicitly |
| TC-001.5 | SR-030 | `frontend/src/auth/LoginPage.test.tsx`, `frontend/src/auth/IdleWarningDialog.test.tsx`, `frontend/src/auth/useIdleTimer.test.ts`, `frontend/src/auth/RequireAuth.test.tsx` | The UI warns before expiry, extends on request and redirects an unauthenticated user | Warning, extend and redirect paths covered |
| TC-001.6 | SR-030 (AC 7) | `backend/tests/auth/test_session_cap_concurrency.py` (`test_concurrent_logins_keep_exactly_the_cap`, 20 repetitions, real Redis `redis:7.4.12-bookworm` container, 10 simultaneous logins at a cap of 3), `backend/tests/auth/test_session_service.py` (`test_cap_holds_over_many_sequential_logins`, `test_cap_transaction_retries_after_concurrent_write`, `test_cap_transaction_gives_up_after_bounded_attempts`, `test_concurrency_cap_evicts_oldest`, `test_new_member_score_above_a_future_scored_member`) | The cap check, eviction and insertion are one optimistic Redis transaction (WATCH/MULTI/EXEC): concurrent logins leave exactly 3 sessions in the account set and as keys, the three pre-existing (oldest) sessions are evicted, every login at the cap evicts exactly one distinct session, and no evicted session key remains; a write between WATCH and EXEC makes the attempt retry; contention that never clears raises after a bounded number of attempts and stores nothing; the score of a new member is never below the newest existing score, so a member scored in the future is the first evicted | All 20 repetitions pass; sequential behaviour unchanged; retry and give-up paths covered |
| TC-001.7 | SR-029 (AC 1), SR-030 (AC 5) | `backend/tests/auth/test_login_service.py` (`test_login_without_lockout_svc_raises_type_error`, `test_login_success_resets_the_lockout_counter`, `test_login_wrong_password_records_the_failure`), `backend/tests/test_config.py` (`test_settings_builds_without_session_signing_key`, `test_stale_session_signing_key_is_ignored`), `mypy app` | The login flow cannot be called without a lockout service (`TypeError` at run time, `call-arg` error from mypy); the app boots without `SESSION_SIGNING_KEY` and ignores a stale one in the environment or `.env` | Omitting `lockout_svc` fails; Settings has no signing-key field and builds with and without a leftover value |
| TC-001.8 | SR-030 (AC 1 to AC 3, AC 5) | `backend/tests/auth/test_session_service.py` (`test_resolve_does_not_recreate_a_deleted_session`, `test_resolve_returns_none_after_invalidate`, `test_resolve_refreshes_ttl_of_a_live_session`), `backend/tests/auth/test_session_cap_concurrency.py` (`test_refresh_racing_invalidate_never_recreates`, `test_refresh_loop_racing_invalidate_leaves_the_session_ended`, 50 repetitions, real Redis), `backend/tests/api/test_auth_router.py` (`TestLogoutEndpoint::test_logout_invalidates_session`) | A session key deleted by logout, eviction or the password-change kill after `resolve()` read it is not written back by the refresh (`SET … EX … XX`), and `resolve()` answers `None`; a live session still gets its sliding TTL | The deterministic case and all 50 racing repetitions leave the key absent and `resolve()` returning `None`; the TTL of a live session is refreshed |
| TC-001.9 | SR-030 (AC 7) | `backend/tests/auth/test_session_service.py` (`test_cap_ignores_expired_members`, `test_cap_evicts_oldest_live_not_dead`), `backend/tests/auth/test_session_cap_concurrency.py` (`test_one_login_with_the_newest_member_expired_evicts_nothing` and `test_concurrent_logins_with_expired_members_keep_cap_of_live`, 20 repetitions each, real Redis; `test_concurrent_logins_keep_exactly_the_cap` unchanged) | Sessions whose key expired are neither counted toward the cap nor chosen for eviction, and are removed from the account set in the same transaction. Arrangement: three sessions at the cap, the NEWEST expired (an expired oldest is evicted by rank anyway and proves nothing). One login evicts nothing and leaves {oldest, middle, new}; 10 simultaneous logins leave exactly 3 members, each with a live key, no expired id, the expired id is never reported as evicted and exactly 2 + 10 - 3 = 9 live sessions are evicted | A login with an expired member evicts nothing; only live sessions are evicted, the oldest first; all 20 + 20 repetitions pass (they fail on the TASK-199 code and on a mutant that counts dead members as live) |
| TC-001.10 | SR-030 (AC 7) | `backend/tests/auth/test_login_service.py` (`test_login_reports_eviction_when_cap_reached`, `test_login_reports_no_eviction_below_cap`), `backend/tests/api/test_auth_router.py` (`TestLoginEndpoint::test_fourth_login_reports_evicted_session`, `TestLoginEndpoint::test_session_cap_contention_returns_503_with_retry_after`), `frontend/src/auth/LoginPage.test.tsx` (eviction notice case, 503 case) | A login that evicted a session answers `evictedSession: true`, any other login `false`, and the login page shows the notice ("Your oldest active session was signed out because the limit of concurrent sessions was reached."); on a 503 the login page says "Sign-in is busy. Please try again." instead of the invalid-credentials message; cap contention answers 503 `application/problem+json` (`session-cap-contention`) with `Retry-After: 1`, sets no session cookie and writes no `LOGIN_SUCCESS` audit row | The first three logins answer `false` and the fourth `true`; the 503 response has all listed properties; the notice text names the oldest active session and the limit; the 503 shows the busy message and not the credentials message |
| TC-001.11 | SR-030 (AC 8, AC 1 to AC 3, AC 4) | `backend/tests/auth/test_session_service.py` (`test_remaining_seconds_is_the_role_inactivity_timeout`, `test_remaining_seconds_is_capped_by_the_absolute_lifetime`, `test_remaining_seconds_is_zero_after_the_absolute_lifetime`), `backend/tests/api/test_me_router.py` (`TestGetMeSessionExpiry`: `test_me_reports_remaining_session_seconds` for DOCTOR, PATIENT, ADMIN and SYSADMIN, `test_me_reports_the_absolute_limit_when_it_is_nearer`), `backend/tests/api/test_auth_router.py` (`test_extend_reports_remaining_seconds`), `frontend/src/auth/SessionActivityProvider.test.tsx` (deadline follows the reported expiry for 30 and 7 minutes; clock skew of +10 and -10 minutes does not move it; an expired session gives one redirect and one `me` request; a mutation's `AuthError`, the upload included, redirects once and clears the cache), `frontend/src/auth/useMe.test.tsx` (no retries; one reader of the `me` query), `frontend/src/api/queryClient.test.tsx` (the handler fires once for concurrent `AuthError`s, again after re-registration, never for other errors), `frontend/src/auth/IdleWarningDialog.test.tsx` (extend deadline from `expiresInSeconds`, not from `expiresAt`), `frontend/src/auth/useIdleTimer.test.ts` (a deadline already in the past is expired); the same `SessionActivityProvider` file also pins the end of the session (15 min reported: warning at 13 min, `/login?timeout=1` at 15 min; a reported 0 is an expired session) and that a wrong current password shows its message with no redirect; `backend/tests/api/test_auth_router.py` (`TestChangePasswordWrongCurrentPassword`: 400 `validation-error` on `currentPassword`, no password change, no audit row, no commit, no session invalidation) | The server reports the remaining session seconds on `GET /me` and extend (role timeout, capped by the absolute lifetime); the client derives its deadline and the 2-minute warning from the receipt time plus that value, with no client timeout constant; a 401 ends the session with one redirect and no repeated session checks | Each backend case asserts the number for its role and limit; the frontend warning appears at reported minus 2 minutes for both reported values and under both clock skews; one redirect and one `me` request on a 401; a wrong current password is a 400, never a 401. Limitation (PRB-087): mouse, key and scroll activity re-arms the client timer but the server slides only on requests, so the client deadline can run ahead of the server's |
| TC-001.12 | SR-030 (AC 1, AC 2, AC 5) | `backend/tests/auth/test_session_no_slide.py`: `test_resolve_without_slide_leaves_ttl_and_last_seen_alone`, `test_resolve_without_slide_returns_none_for_missing`, `test_resolve_without_slide_enforces_absolute_expiry`, `test_polling_my_modules_does_not_extend_the_session`, `test_my_modules_with_an_expired_session_is_401`, `test_my_modules_with_a_session_past_its_absolute_lifetime_is_401`, `test_my_modules_with_an_ended_session_is_401`, `test_my_modules_for_an_inactive_account_is_401`, `test_my_modules_without_a_cookie_is_401`, `test_other_routes_still_slide_the_session` (TASK-221, RISK-005) | `GET /me/modules`, which the client polls on a timer, validates the session but does not extend it: the Redis TTL and the stored `last_seen_at` are unchanged after repeated polls; an expired, absolutely expired, ended (invalidated) or missing session and an inactive account are answered 401; `GET /me` still slides the session | All listed tests pass; with `GET /me/modules` switched back to the sliding dependency, or with `resolve(slide=False)` still sliding, the polling test fails (and the service test in the second case) |

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
- 1.4 (2026-11-06) — TASK-205 (CR-004 D-11): added TC-001.8 (refresh never re-creates an ended session, PRB-064), TC-001.9 (expired members pruned from the cap, oldest live evicted, PRB-065) and TC-001.10 (eviction reported, cap contention answered 503, PRB-066); TC-001.6 gains the score-rule test (TASK-199 QA finding 1). Content changed, so the 1.3 approval no longer applies: status set to `in_review` for re-approval.
- 1.4 (2026-11-07) — TASK-205 round 2 (QA): TC-001.9 rearranged so the newest member is the expired one (the earlier arrangement passed on the TASK-199 code), with the evicted-id assertions and a single-login case; TC-001.10 gains the 503 login-page case and the neutral notice text. Still `in_review`.
- 1.4 (2026-11-07) — QA review (TASK-205 round 2): approved (`in_review → approved`). TC-001.8 to TC-001.10 run by QA: real-Redis file 3 × 111 passed; the TC-001.9 real-Redis cases fail 40/40 on f254277 and on the dead-as-live mutant.
- 1.5 (2026-11-14) — TASK-144 (CR-006, PRB-016): added TC-001.11 (server-reported session expiry, client deadline, one redirect on a 401). Content change, so the 1.4 approval record is cleared and the record returns to review.
- 1.5 (2026-11-14) — TASK-144 QA round 1: TC-001.11 gains the session-end test, the reported-0 and past-deadline cases, the wrong-current-password cases (400, not 401) and the PRB-087 limitation. Still `in_review`.
- 1.5 (2026-11-14) — QA review of TASK-144 (round 2): `approved` (status only; content unchanged).
- 1.6 (2026-11-14): TASK-221 round 2. Added TC-001.12 (the module-list poll does not extend the session). Content change, so the approval record is removed. `in_review`.
- 1.6 (2026-11-14) — QA review of TASK-221 (round 2): `approved` (status only; content unchanged).
