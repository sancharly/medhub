---
id: "PRB-089"
type: problem-report
title: "Client inactivity timeout neither ends the server session nor clears the cached clinical data"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-14"
updated: "2026-11-15"
criticality: major
links: []
tags: ["session", "frontend", "privacy", "found-in:TASK-221-qa"]
---

# PRB-089 — Client inactivity timeout neither ends the server session nor clears the cached clinical data

## Observed

QA found this in the TASK-221 review round 1 (HIGH 1, 2026-11-14), and it was raised to the human as CR-006 P-18. When the client inactivity deadline passes, `handleExpired` (`frontend/src/auth/SessionActivityProvider.tsx:39-42`) hides the warning and navigates to `/login?timeout=1`. Nothing else happens:

- It does not call `apiClient.logout()`, so the server session is not invalidated.
- It does not call `qc.clear()`, so the TanStack Query cache keeps every response the user loaded, the `me` query and the clinical views included.

The two handlers that end a session the other ways already do both. The `AuthError` handler a few lines below clears the cache and redirects. The dialog's `handleLogout` calls `apiClient.logout()` and then `qc.clear()`. The behaviour predates CR-006.

## Impact

At an unattended workstation, after the client has redirected to sign-in:

- Going Back, or to `/`, re-mounts the authenticated layout. `RequireAuth` (`frontend/src/auth/RequireAuth.tsx`) finds the `me` query still in success state with data, so it renders the cached views. The clinical data the user last viewed is shown again with no re-authentication.
- If the server session is still alive, the person at the workstation has a working session. Any request they make slides it further, and they can read and write as the signed-in user.
  - The session can be alive at the client deadline when the user made requests after the last `me` or extend response. Under CR-006 D-33 (PRB-087: the client deadline comes only from those responses) this is the normal case, not an edge case.
  - It was also the case before D-32, when the module poll kept the session alive.
- If the server session has ended, the cached data stays on screen until a refetch answers 401 and `RequireAuth` redirects. If that refetch fails for another reason (network down, 5xx), `RequireAuth` keeps the app mounted with the cached data (PRB-067 behaviour), and the data stays on screen.

## Investigation

`useIdleTimer` calls `onExpired` when the deadline timer fires, or at once for a deadline already in the past. `onExpired` is `handleExpired`, which only navigates. The root cause is that the expiry path was written as a redirect, not as a session end. The `AuthError` path (PRB-016, TASK-144) and the explicit logout path were each given their own cleanup, and the timeout path was never aligned with them.

What does not reach the cached data:

- A server-side 401 on a query: `RequireAuth` returns `null` on `AuthError`.
- A 401 on a mutation: the `AuthError` handler clears the cache.

## Safety evaluation

- **Privacy, RISK-001.** Protected health information is shown to a person at the workstation who has no right to it: the next user, a visitor or another patient. Only data the authorized user already loaded is shown while the server session has ended. Anything the live session can reach is exposed while it has not. Severity 2 (privacy harm, a possible GDPR breach). No physical injury.
- **Account takeover, RISK-005.** While the server session is alive, someone else can act as the signed-in clinician, including writing clinical entries under their name. That is the RISK-005 harm, severity 3, recoverable through the audit trail. The SR-030 AC 1 and AC 2 control is undermined whenever the client deadline is the earlier one, which D-33 makes the normal case.
- **Criticality `major`** (human decision, CR-006 D-33, "Major, in CR-006"). The failure defeats an implemented risk control, not just the clinical workflow. No released version is in clinical use; only development data exists (CR-004 D-21), so no notification is needed.

## Resolution

Fixed in CR-006 by TASK-222 in `frontend/src/auth/SessionActivityProvider.tsx` (`handleExpired`):

1. It starts `apiClient.logout()` and does not await it. The result is ignored (an already-ended session answers 401), and it is never passed to the mutation `AuthError` handler, so no second redirect follows.
2. It redirects once to `/login?timeout=1`.
3. The query cache is cleared by the provider's unmount cleanup, as that redirect removes the signed-in tree. Clearing it earlier, with `me` observers still mounted, makes them recreate the query and send a second `GET /me` after the redirect (found while writing the tests; SR-030 AC 8). Back therefore finds no cached clinical data, and `RequireAuth` renders nothing until `me` answers.

Tests (TS-001 TC-001.13): `timeout logs out, clears the cache and redirects once`, `timeout still clears and redirects when logout fails` (401 and network error), `redirects without waiting for logout to answer`, `Back after a timeout shows no clinical data`. The system-level check that the server refuses the session cookie after a client timeout is TS-001 TC-001.14, pending (needs a started stack). The dialog's own redirect paths are PRB-090.

Verified 2026-11-14 in the working tree: `npm test -- --run` (35 files, 361 tests), `npm run typecheck`, `npm run lint`, `npm run build` clean; the six negative controls of TASK-222 each fail at least one test (TS-001 TC-001.13). Not yet confirmed through a shipped release, so the status is `resolved`, not `closed`.

**TASK-226 verification (2026-11-15), started stack, script level:** after the `POST /auth/logout` that a client timeout performs, `GET /me` and `GET /me/modules` with the old session cookie answer 401. TS-001 TC-001.14. The browser half (idle past the deadline, then Back) is covered by the unit tests of TC-001.13, not by a browser run. Stays `resolved`.
