---
id: "PRB-088"
type: problem-report
title: "A failed current-password check on POST /auth/password is neither audited nor attempt-limited"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-14"
updated: "2026-11-14"
criticality: minor
links: []
tags: ["auth", "audit", "backend", "found-in:TASK-144-qa"]
---

# PRB-088 — A failed current-password check on POST /auth/password is neither audited nor attempt-limited

## Observed

Found by QA in the TASK-144 review (2026-11-14). `POST /auth/password` re-authenticates the signed-in user with the current password. When that check fails the endpoint answers 400 `validation-error` on `currentPassword` and nothing else happens: no audit event is written and the failure is not counted against any attempt limit. The behaviour predates CR-006; TASK-144 only changed the status code from 401 to 400 so the mutation handler would not end the session. The test `test_wrong_current_password_changes_nothing_and_audits_nothing` in `backend/tests/api/test_auth_router.py` pins today's behaviour.

The same test has a vacuous assertion: `mock_svc.invalidate.assert_not_called()` passes whatever the endpoint does, because the mocked `list_account_session_ids` iterates as empty, so `invalidate` could never be called. It should assert `list_account_session_ids.assert_not_called()`. It was not changed here.

## Impact

- A session held by someone other than the account owner (a left-open workstation, a stolen cookie) can guess the current password through this endpoint without limit and without a trace. A correct guess lets that person set a new password and lock the owner out.
- The failures cannot be reconstructed from the audit log.

## Investigation

`change_password` (`backend/app/api/routers/auth.py:137`) verifies the current password at line 155 and, on failure, raises `ValidationProblem` (400, rule `CURRENT_PASSWORD_INCORRECT`) straight away. The handler builds no `AuditService` and no `LockoutService`; the login handler (same file, lines 48-72) builds both and passes the lockout service to `LoginService.login`, which records success and failure and applies the SR-029 lockout. The root cause is a gap in scope, not a regression: SR-029 describes the lockout for login only, and whether SR-023 AC 1 covers this re-authentication is not settled.

## Safety evaluation

No data integrity, safety-related function or clinical decision is affected directly. The exposure is account takeover by someone who already holds a signed-in session, which is a RISK-005 concern, bounded by the session timeout (SR-030) and by the 8 hour absolute limit. No access beyond the account's own is gained. Criticality `minor`. A released version in use has the same behaviour, so no new notification arises from this report.

**Open decision for a human:** SR-023 AC 1 says "authentication attempts (success and failure) are recorded". It may be read to cover this re-authentication, in which case the missing audit event is a defect against SR-023. If it is not, the audit and the limit are new requirements (an SR-023 or SR-029 change with its own change request). SR-029's lockout covers login only. This record does not take that decision.

## Resolution

Not fixed here, and outside CR-006. After the human decides the scope of SR-023 and SR-029: record the failed check as an audit event and count it toward an attempt limit, then change the vacuous assertion of `test_wrong_current_password_changes_nothing_and_audits_nothing` to `list_account_session_ids.assert_not_called()` and update the test to the new behaviour. Verify with a test that N wrong current passwords produce N audit events and, at the limit, a refusal.
