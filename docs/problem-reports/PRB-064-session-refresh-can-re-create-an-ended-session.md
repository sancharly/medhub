---
id: "PRB-064"
type: problem-report
title: "Session refresh can re-create a session that logout, eviction or a password change ended"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-06"
updated: "2026-11-07"
criticality: major
links: []
tags: ["auth", "session", "hazard:security", "found-in:TASK-199-qa"]
---

# PRB-064 — Session refresh can re-create a session that logout, eviction or a password change ended

## Observed

Found by QA while reviewing TASK-199 (2026-11-06, commit f254277). `SessionService.resolve()` reads the
session key and then rewrites it with `SETEX` to slide the inactivity TTL. When another request deletes
the key between those two calls (a logout, an eviction by the concurrent-session cap, or the
"invalidate other sessions" loop of a password change), the `SETEX` writes the key again. The session is
then valid again, but its id is no longer in the account's sorted set. QA reproduced this
deterministically with fakeredis by deleting the key between the `GET` and the `SETEX`. Present before
TASK-199; TASK-199 did not change `resolve()`.

## Impact

A session that the system has ended can be used again until its inactivity timeout:

- **Logout (SR-030 AC 5):** a request carrying the same token that is in flight while the user logs out
  can bring the token back, so it "can be reused" after logout.
- **Password change:** the loop that invalidates the other sessions reads the account set; a re-created
  session is not in it, so it survives the password change. Ending the other sessions on a password
  change is the step a user takes when they suspect a stolen session (RISK-005).
- **Cap (SR-030 AC 7):** a re-created session is outside the account set, so it is not counted and is
  never evicted. The account can then hold more than 3 live sessions.

The window is the time between two Redis round trips of one request, so an accidental occurrence is
rare. An attacker who holds a stolen token can keep sending requests to widen the chance of winning the
race at the moment the victim logs out or changes the password.

## Investigation

- `backend/app/auth/session.py:158` — `resolve()` reads `session:{id}` with `GET`.
- `backend/app/auth/session.py:186-188` — it writes the same key back with
  `SETEX key effective_ttl payload`. `SETEX` creates the key when it is absent; nothing makes the write
  conditional on the key still existing.
- Callers that delete the key concurrently:
  - `session.py:191-199` `invalidate()` (logout at `backend/app/api/routers/auth.py:100`; the
    password-change loop at `auth.py:160-162`);
  - `session.py:142-143` the eviction inside the cap transaction (TASK-199);
  - `session.py:215-222` `invalidate_all()` (deactivation `identity/lifecycle.py:63`, erasure
    `identity/erasure.py:116`, worker `workers/session_tasks.py:44`).
- For deactivation and erasure the re-created session is still refused, because `get_current_user`
  requires an `ACTIVE` account (`backend/app/api/deps.py:81-82`). For logout, password change and
  eviction the account stays active, so nothing else refuses the session.
- Root cause: the refresh is an unconditional write where a conditional one is required. Redis
  `SET key value EX ttl XX` writes only when the key exists and is atomic. It closes the window without
  a transaction.

## Safety evaluation

Confidentiality and integrity: an ended session that is still usable can read PHI or write clinical
entries in the user's name (RISK-005, account takeover; harm severity 3). It weakens the logout (SR-030
AC 5), the password-change session kill and the concurrent-session cap (SR-030 AC 7) controls. It is not a
direct safety function and it needs a race, so it is not `critical`. Criticality **major**: a security
control can be defeated by a user holding a stolen token. No release exists (CR-004 A-1), so no released
version in use is affected and no notification is needed. The human sets the final criticality.

## Resolution

Fixed in CR-004 by TASK-205 (QA-approved 2026-11-07; `resolved`, D-8). `SessionService.resolve()` now refreshes with `SET key payload EX ttl XX` (`set(..., xx=True)`): Redis writes only if the key still exists, in one atomic command, so no transaction is needed. A nil reply means the key was deleted after the `GET` (logout, eviction, password-change kill); `resolve()` returns `None` and the request is answered 401. Verified by TS-001 TC-001.8: a deterministic test (a proxy that deletes the key right after the `GET`) with fakeredis and with real Redis, and a racing-thread test of 50 repetitions on real Redis. Both fail on the TASK-199 `resolve()` (f254277) and when `xx=True` is removed.

## Source

TASK-199 QA review round 1 (`docs/design-outputs/tasks/TASK-199-atomic-concurrent-session-cap.md`,
"Not introduced here"); human decision 2026-11-06 to open it and fold it into CR-004.

## Version history

- 1.0 (2026-11-06) — Created from the TASK-199 QA review. `open`, `major`.
- 1.1 (2026-11-06) — Resolution written (TASK-205). Status stays `open` until QA approval (CR-004 D-8).
- 1.1 (2026-11-07) — QA review (TASK-205 round 2): approved; status `open → resolved` (D-8). CR-004 `resolves` PRB-064. Criticality unchanged.
