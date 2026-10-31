---
id: "PRB-023"
type: problem-report
title: "Concurrent-session cap eviction is not atomic"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-31"
criticality: major
links: []
tags: ["correctness", "hazard:security"]
---

# PRB-023 — Concurrent-session cap eviction is not atomic

## Observed

`app/auth/session.py:97` implements the concurrency cap as a multi-step read-then-write sequence against Redis with no transaction, so two simultaneous logins can both pass the cap or evict the wrong session.

## Impact

The SR-030 concurrent-session limit is not reliably enforced.

## Investigation

Read on 2026-10-31 (CR-004 Plan stage, Software Architect role). **Present as reported.**

- `SessionService.create_session` (`backend/app/auth/session.py:95-112`) runs six separate Redis
  commands: `ZRANGE` of the account's sessions, then, at the cap, `DELETE` and `ZREM` of the
  oldest, then `SETEX`, `ZADD` and `EXPIRE` for the new one. Nothing makes them one operation.
- Two logins for one account at the cap (3 sessions) both read the same three ids, both evict
  the same oldest one, and both add their own: 4 sessions remain, contrary to SR-030 AC 7. With a
  login and an eviction interleaved differently, an attacker's session can survive the eviction
  that should have removed it.
- No test runs concurrent logins; the unit tests use `fakeredis` sequentially
  (`backend/tests/auth/test_session_service.py`).

## Safety evaluation

Contributes to RISK-005 (account takeover: an attacker session survives an eviction meant to remove it).

## Resolution

Planned in CR-004: TASK-199 (cap check, eviction and insertion in one optimistic Redis
transaction, with a concurrency test against a real Redis server). Not yet fixed.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Performance.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
