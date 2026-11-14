---
id: "PRB-087"
type: problem-report
title: "Client idle timer re-arms on user activity while the server session slides only on requests"
status: resolved
version: "1.1"
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

Fixed in CR-006 by TASK-222 with option 1 (human decision D-33, "Server responses only"). `useIdleTimer` takes its deadline only from `deadlineOverride`, which `SessionActivityProvider` derives as the receipt time of the newest `me` or extend response plus the session seconds that response reports. The activity listeners and `resetDeadline` are removed (`frontend/src/auth/useIdleTimer.ts`), and the `timeoutSeconds` option with them. To keep the session the user makes a request that refreshes `me`, or presses Extend (SR-030 AC 4, AC 8). The client deadline can no longer run ahead of the server's, and near the 8 hour absolute limit it follows the capped server value.

Tests (TS-001 TC-001.5, TC-001.13): `useIdleTimer.test.ts` `activity events do not move the deadline`, `a new deadline re-arms both timers`; `SessionActivityProvider.test.tsx` `reading without requests is warned at 13 min and signed out at 15 min`, `Extend re-arms from expiresInSeconds`, `a refreshed me re-arms`.

Verified 2026-11-14 in the working tree: `npm test -- --run` (35 files, 361 tests), `npm run typecheck`, `npm run lint`, `npm run build` clean; the six negative controls of TASK-222 each fail at least one test (TS-001 TC-001.13). Not yet confirmed through a shipped release, so the status is `resolved`, not `closed`.
