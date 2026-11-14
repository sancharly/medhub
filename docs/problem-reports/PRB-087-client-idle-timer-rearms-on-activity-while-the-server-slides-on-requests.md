---
id: "PRB-087"
type: problem-report
title: "Client idle timer re-arms on user activity while the server session slides only on requests"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-14"
updated: "2026-11-14"
criticality: minor
links: []
tags: ["session", "frontend", "found-in:TASK-144-qa"]
---

# PRB-087 — Client idle timer re-arms on user activity while the server session slides only on requests

## Observed

Found by QA in the TASK-144 review (2026-11-14). `useIdleTimer` re-arms the client deadline to now plus the reported session length on every mouse, key,
touch or scroll event (`frontend/src/auth/useIdleTimer.ts`, `resetDeadline`, bound at lines 54-60). The server, however, slides the session only when a
request reaches it (`SessionService.resolve`). The behaviour predates TASK-144 (the old code re-armed to a 15-minute constant). It is not covered by
PRB-017 (missing unit tests) or TASK-222 (re-arming at most once per second).

## Impact

- A user who moves the mouse or scrolls without making a request for longer than the timeout gets no warning (SR-030 AC 4); the server session has
  already ended, so the next action is answered 401 and the user is redirected to sign-in.
- Near the 8 hour absolute limit, activity re-arms the client past the absolute end (the server value is capped, the re-arm is not recomputed from it).

The server control of RISK-005 still holds (the session ends on the server); the client only misreports how long it has left.

## Investigation

`resetDeadline` computes `Date.now() + timeoutSeconds * 1000` from the length reported by the last `me` or extend response and reschedules the warning and
expiry timers. Nothing tells the server about the activity, and the client deadline is not re-derived from a server response after the re-arm.

## Safety evaluation

No data integrity, safety-related function or clinical decision is affected. The effect is a missing warning and a surprise sign-in redirect, never
access beyond the server's decision. No release in use is affected beyond this existing behaviour, so no notification is needed. Criticality `minor`.

## Resolution

Not fixed here, and outside CR-006. Two options; the choice belongs to the human and must be coordinated with TASK-222 (activity throttling):

1. Re-arm the client deadline only from server responses (`me` and extend), not from activity events.
2. Make activity call the server through a throttled extend request, so the server and the client slide together.

Verify with a test that mouse activity without requests does not move the client deadline (option 1), or that activity causes at most one extend call per
throttle window and the deadline follows the response (option 2), including a case near the absolute limit.
