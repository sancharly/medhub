---
id: "TASK-220"
type: task
title: "Constant-query group membership lookup, guarded by a characterisation test"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-13"
links:
  - target: "SR-026"
    relation: implements
  - target: "SR-014"
    relation: implements
  - target: "RISK-004"
    relation: mitigates
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-024"
    relation: relates_to
  - target: "ADD-009"
    relation: relates_to
  - target: "TS-005"
    relation: relates_to
  - target: "RISK-001"
    relation: relates_to
tags: ["cr:CR-006", "performance", "control:protective"]
---

# TASK-220 — Constant-query group membership lookup, guarded by a characterisation test

- **Software item / unit:** SI-GROUPS `GroupService.groups_of` (ADD-009); group repository (ADD-016).
- **PRB:** PRB-024. **CR:** CR-006 (change-analysis cause 5).
- **Depends on:** none (parallel).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** S (`backend/app/groups/service.py`, `backend/app/db/repositories/group_repo.py`; tests
  `backend/tests/groups/test_groups_of.py`; records TS-005, TS-018).

## Objective

SR-026 AC 6: listing a user's groups issues a constant number of queries, independent of the number of
memberships. `groups_of` (`groups/service.py:131-138`) calls `self._group_repo.get(m.group_id)` once per
membership. RISK-004 control: the result set must not change (no enabled module newly denied; RISK-001: none
newly shown), so a characterisation test is written and committed **before** the rewrite.

## Implementation detail

1. **First commit-ready step:** `test_groups_of_characterisation` (SR-014 AC 4, SR-015 AC 3): accounts with 0,
   1, several MANUAL and AUTO memberships, a membership whose group was deleted (today skipped), duplicate
   group through two sources; assert the exact set and order of returned group ids. Green on the current code.
2. `GroupRepository.groups_for_account(account_id) -> list[Group]`: one `select(Group).join(GroupMembership)
   .where(GroupMembership.account_id == account_id)`; deduplicate and order as today (characterisation
   decides; document the order rule).
3. `groups_of` uses it; `memberships_for_account` stays for its other callers.

## Tests (write first)

- `test_groups_of_characterisation` (SR-014 AC 4) unchanged before and after the rewrite.
- `test_groups_of_query_count_constant` (SR-026 AC 6): SQLAlchemy `before_cursor_execute` counter; queries for
  1, 10 and 100 memberships are equal.
- Existing module-enablement tests (SR-015 AC 3, AC 4) unchanged.
- Recorded in TS-005 (first CR-006 task to change it: 1.1 → 1.2, approval cleared; TC-005.x characterisation)
  and TS-018 (TC-018.6 query count).

## Acceptance criteria

- [ ] SR-026 AC 6: constant queries at 1, 10, 100 memberships.
- [ ] SR-014 AC 4 / RISK-004: characterisation test identical before and after.

## Definition of Done

- [ ] `ruff`, `mypy`, backend suite green
- [ ] TS-005, TS-018 updated; ADD-009 consistent
- [ ] `traceability-check` no error for this record

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect) for PRB-024.
