---
id: "PRB-088"
type: problem-report
title: "A failed current-password check on POST /auth/password is neither audited nor attempt-limited"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-14"
updated: "2026-11-16"
criticality: minor
links:
  - target: "SR-023"
    relation: relates_to
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

`change_password` (`backend/app/api/routers/auth.py:137`) verifies the current password at line 155 and, on failure, raises `ValidationProblem` (400, rule `CURRENT_PASSWORD_INCORRECT`) straight away. The handler builds no `AuditService` and no `LockoutService`; the login handler (same file, lines 48-72) builds both and passes the lockout service to `LoginService.login`, which records success and failure and applies the SR-029 lockout. The root cause is a gap in scope, not a regression: SR-029 describes the lockout for login only, and whether SR-023 AC 1 covers this re-authentication was not settled when the report was raised (settled by CR-006 D-38, below).

## Safety evaluation

No data integrity, safety-related function or clinical decision is affected directly. The exposure is account takeover by someone who already holds a signed-in session, which is a RISK-005 concern, bounded by the session timeout (SR-030) and by the 8 hour absolute limit. No access beyond the account's own is gained. Criticality `minor`. A released version in use has the same behaviour, so no new notification arises from this report.

**Decision (human, Carlos Santiago Liceras, 2026-11-16, CR-006 D-38, answer "Defect, fix later"):** SR-023 AC 1 ("authentication attempts (success and failure) are recorded") is read as covering the re-authentication on `POST /auth/password`. The missing audit event for a failed current-password check is therefore a defect against SR-023 AC 1, not a new requirement. The report stays `open` and `minor`, outside CR-006, and is resolved by a later change request. The decision does not extend SR-029: its lockout covers login only, so counting the failures toward an attempt limit is not required by an approved criterion today. The later change request decides whether to add it, which needs an SR-029 change.

## Resolution

Not fixed here, and outside CR-006 (D-38). In the later change request: record each failed current-password check as an audit event (SR-023 AC 1) and verify with a test that N wrong current passwords produce N audit events. If that change request also takes the attempt limit (SR-029 change first), verify that the limit refuses further checks. Change the vacuous assertion of `test_wrong_current_password_changes_nothing_and_audits_nothing` to `list_account_session_ids.assert_not_called()` and update the test to the new behaviour.

## Version history

- 1.0 (2026-11-14) — Raised from the TASK-144 QA review. `open`, `minor`.
- 1.1 (2026-11-16) — CR-006 D-38: the human read SR-023 AC 1 as covering this re-authentication, so the missing audit event is a defect against SR-023, fixed by a later change request. "Open decision for a human" replaced by the decision; Resolution updated; `relates_to` SR-023 added. Stays `open`, `minor`.
