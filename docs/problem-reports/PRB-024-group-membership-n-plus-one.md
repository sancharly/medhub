---
id: "PRB-024"
type: problem-report
title: "Group membership lookup issues one query per membership"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-14"
criticality: minor
links: []
tags: ["performance"]
---

# PRB-024 — Group membership lookup issues one query per membership

## Observed

`app/groups/service.py:134-138` (before TASK-220) — `groups_of` called `GroupRepository.get()` once per membership row
instead of one joined query. QA of TASK-220 (2026-11-14) found that `groups_of` has no caller in `backend/app/` or
`backend/modules/`.

## Impact

Latent: the cost grew with the membership count (`{1: 3, 10: 12, 100: 102}` queries), but no request path called
the method. Module gating does not use it and already issued a constant number of queries (3 at 1, 10 and 100
memberships). The original statement that it affected module gating was wrong.

## Investigation

`groups_of` (`groups/service.py:134`) is only defined, never called. The module-gating paths use other calls:
`ModuleAccessGuard.is_module_enabled` (`authz/module_guard.py:16-27`, called from `api/deps.py:179` for every module
route) and `GET /me/modules` (`api/routers/me.py:33-35`) both use `memberships_for_account` plus
`enabled_module_keys_for_groups`, a constant number of queries. The per-membership `get()` loop was the only N+1.

## Safety evaluation

No hazard beyond the general latency contribution in RISK-007; no request path is affected.

## Resolution

TASK-220 (CR-006): `GroupRepository.groups_for_account` (`db/repositories/group_repo.py:54-61`, one joined query) and
`groups_of` using it (`groups/service.py:134-136`). Verified by `backend/tests/groups/test_groups_of.py`:
`test_groups_of_characterisation` (same result set, green before and after) and
`test_groups_of_query_count_constant` (equal count at 1, 10 and 100 memberships; on `c69d7dc` it fails with
`{1: 3, 10: 12, 100: 102}`). `test_module_gate_query_count_constant` guards the module-gating paths (it fails with
`{1: 4, 10: 13, 100: 103}` when an N+1 is planted in the guard). The fix is preventive: no hot path changed.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Performance.

## Version history

- 1.0 (2026-10-21): Created from the audit findings.
- 1.1 (2026-11-14): TASK-220 QA round 1: premise corrected (latent, `groups_of` unused), Investigation and Resolution added. Still `open`.
- 1.2 (2026-11-14): QA review of TASK-220 (round 2): APPROVED; fix verified, `open → resolved` (CR-006 holds the `resolves` link).
