---
id: "PRB-066"
type: problem-report
title: "Login always reports no evicted session, so the eviction notice is never shown"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-06"
updated: "2026-11-07"
criticality: minor
links: []
tags: ["auth", "session", "frontend", "found-in:TASK-199-qa"]
---

# PRB-066 — Login always reports no evicted session, so the eviction notice is never shown

## Observed

Found by QA while reviewing TASK-199 (2026-11-06, commit f254277). `POST /api/v1/auth/login` answers
`"evictedSession": false` on every successful login, including a fourth login that has just ended the
account's oldest session. The frontend's eviction notice therefore never appears.

## Impact

SR-030 AC 7: opening a fourth session invalidates the oldest active session "and presents a notification
to the user". The invalidation happens; the notification does not. A user who signs in on a fourth
workstation is not told that another session was ended. The person on the ended session only sees a
sign-in prompt at their next request.

## Investigation

- `backend/app/auth/session.py:104-106` — `create_session()` returns `CreateSessionResult` with
  `evicted_session_id` set when a session was evicted (TASK-199 keeps this meaning).
- `backend/app/auth/login.py:126` — `LoginService.login` calls `create_session` and, at
  `login.py:138`, returns `LoginSuccess(session=..., csrf_token=...)`. `LoginSuccess`
  (`login.py:31-35`) has no field for the eviction, so the information is dropped here.
- `backend/app/api/routers/auth.py:86` — the route hard-codes `evicted_session=False` in
  `LoginResponse` (schema field `backend/app/api/schemas/auth.py:39`).
- Frontend, already correct: `frontend/src/auth/LoginPage.tsx:34-37` shows the notice and waits for
  "Continue" when `evictedSession` is true, and `LoginPage.tsx:61-71` renders it;
  `frontend/src/auth/LoginPage.test.tsx:130` covers it. The generated type carries `evictedSession`.
  Only the backend is wrong.
- Root cause: the flag was never wired from the session service through the login service to the route.

## Safety evaluation

No data is disclosed, altered or lost. The eviction itself works. The missing notice reduces the user's
awareness of their own sessions, which is a weak detection aid against account takeover (RISK-005), not a
control the residual estimate relies on. Criticality **minor**. No release exists (CR-004 A-1), so no
notification is needed. The human sets the final criticality.

## Resolution

Fixed in CR-004 by TASK-205 (QA-approved 2026-11-07; `resolved`, D-8). `LoginSuccess` has `evicted_session: bool`, set by `LoginService.login` from `result.evicted_session_id is not None`; `POST /auth/login` returns it as `evictedSession` instead of the constant `False`. The login page already showed a notice; its text ("Your previous session was ended because you signed in elsewhere.") was inaccurate and now reads "Your oldest active session was signed out because the limit of concurrent sessions was reached." (round-2 wording); a 503 at login shows "Sign-in is busy. Please try again." instead of the credentials error. Verified by TS-001 TC-001.10: the first three logins answer `false` and the fourth `true`; the router test fails when the route returns `False` again.

## Source

TASK-199 QA review round 1; human decision 2026-11-06 to open it and fold it into CR-004.

## Version history

- 1.0 (2026-11-06) — Created from the TASK-199 QA review. `open`, `minor`.
- 1.1 (2026-11-06) — Resolution written (TASK-205). Status stays `open` until QA approval (CR-004 D-8).
- 1.1 (2026-11-07) — QA review (TASK-205 round 2): approved; status `open → resolved` (D-8). CR-004 `resolves` PRB-066. Criticality unchanged. Resolution: notice text aligned with the round-2 wording and the 503 message added (QA).
