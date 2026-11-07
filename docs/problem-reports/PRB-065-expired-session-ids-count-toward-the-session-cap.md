---
id: "PRB-065"
type: problem-report
title: "Expired session ids count toward the concurrent-session cap and make a live session be evicted"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-06"
updated: "2026-11-07"
criticality: minor
links: []
tags: ["auth", "session", "hazard:availability", "found-in:TASK-199-qa"]
---

# PRB-065 — Expired session ids count toward the concurrent-session cap and make a live session be evicted

## Observed

Found by QA while reviewing TASK-199 (2026-11-06, commit f254277). When a session expires by inactivity,
its key `session:{id}` disappears through its Redis TTL, but its id stays in the sorted set
`account_sessions:{account_id}`. The cap counts every member of the set. At the next login over the cap
the oldest members are evicted by rank, so a live session can be ended while a dead id that is older or
newer stays in the set. The behaviour was the same before TASK-199.

## Impact

SR-030 AC 7 says that a fourth session invalidates the **oldest active** session. Today:

- Example: the set holds A (oldest, live), B (dead by inactivity) and C (live). A new login counts 3
  members, evicts the lowest-ranked one, A, and keeps the dead B. Only two live sessions remained, so
  no eviction was needed at all.
- The user loses a session on another workstation for no reason.

The cap is never exceeded by this defect: dead members only make it stricter. No session is kept alive
that should end.

## Investigation

- `backend/app/auth/session.py:127-130` — the cap transaction reads every member of the account set
  with `ZRANGE … WITHSCORES`.
- `session.py:139` — `evicted = ids[: max(0, len(ids) + 1 - self._max_concurrent)]` counts all members,
  live or not, and evicts by rank.
- `session.py:144` — the session key gets the inactivity TTL (15 or 30 min); `session.py:147` — the set
  gets the absolute lifetime (8 h) and is refreshed on every login. Nothing removes a member whose key
  expired. `invalidate()` (`session.py:191-199`) removes the member only on an explicit logout.
- `list_account_session_ids()` (`session.py:201-205`) also returns dead ids; the password-change loop
  (`backend/app/api/routers/auth.py:160-162`) then deletes keys that are already gone, which is
  harmless.
- Root cause: the set is treated as the list of active sessions, but membership is not kept in step with
  key expiry. A dead member must be pruned (or skipped) before counting, inside the same WATCH/MULTI/EXEC
  transaction.

## Safety evaluation

Availability only, and mild: a clinician may have to sign in again on another workstation. No data is
disclosed, altered or lost, and no security control is weakened (the cap only becomes stricter).
Criticality **minor**. The requirement SR-030 AC 7 ("oldest active") is not met. No release exists
(CR-004 A-1), so no notification is needed. The human sets the final criticality.

## Resolution

Fixed in CR-004 by TASK-205 (QA-approved 2026-11-07; `resolved`, D-8). Inside the TASK-199 `WATCH`/`MULTI`/`EXEC` transaction, after reading the set, one `EXISTS session:{id}` per member (immediate mode, before `MULTI`) separates live from dead ids. The cap counts and evicts live ids only (`live_ids[: max(0, len(live_ids) + 1 - cap)]`), and `MULTI` also queues `ZREM` of the dead ids. No watch on the member keys is needed: after PRB-064 a deleted session key is never written again, so a key found missing stays missing; one that expires between `EXISTS` and `EXEC` is counted live once more and at worst a dead session is evicted. Verified by TS-001 TC-001.9 (fakeredis and 20 repetitions of 10 simultaneous logins on real Redis). The real-Redis cases (the newest member expired, so rank-based eviction cannot hide it) and the fakeredis cases fail on f254277, on a mutant that counts dead members as live, and when the `ZREM` of dead ids is removed.

## Source

TASK-199 QA review round 1; human decision 2026-11-06 to open it and fold it into CR-004.

## Version history

- 1.0 (2026-11-06) — Created from the TASK-199 QA review. `open`, `minor`.
- 1.1 (2026-11-06) — Resolution written (TASK-205). Status stays `open` until QA approval (CR-004 D-8).
- 1.2 (2026-11-07) — Resolution: verification arrangement corrected after QA round 1 of TASK-205. Status stays `open`.
- 1.2 (2026-11-07) — QA review (TASK-205 round 2): approved; status `open → resolved` (D-8). CR-004 `resolves` PRB-065. Criticality unchanged.
