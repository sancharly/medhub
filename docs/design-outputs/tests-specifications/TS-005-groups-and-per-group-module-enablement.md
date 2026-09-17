---
id: "TS-005"
type: test-specification
title: "Groups and per-group module enablement verification"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links:
  - target: "SR-014"
    relation: verifies
  - target: "SR-015"
    relation: verifies
tags: ["level:unit", "class:B"]
---

# TS-005 — Groups and per-group module enablement verification

## Scope

Software requirements covered: SR-014, SR-015.
Software items under test: SI-GROUPS, SI-AUTHZ, SI-FE-CORE, SI-FE-MODREG.
Levels: unit, integration.

## Preconditions and environment

Build: branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 20 with `frontend/package-lock.json`.
Unit and service tests run with no external services (in-memory repositories). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: [ADD-004](../architecture/ADD-004-soup-list.md).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-005.1 | SR-014 | `backend/tests/groups/test_group_service.py`, `backend/tests/groups/test_membership.py`, `backend/tests/api/test_groups_router.py` | Group CRUD works; membership is assigned automatically by user type and manually | Name uniqueness enforced; both membership paths covered |
| TC-005.2 | SR-015 | `backend/tests/groups/test_module_enablement.py`, `backend/tests/authz/test_module_guard.py`, `backend/tests/modules/test_module_gating.py` | A module is reachable only for groups where it is enabled | Disabled group receives a denial, not an empty success |
| TC-005.3 | SR-014, SR-015 | `frontend/src/core/admin/groups/GroupsPage.test.tsx` | The admin UI creates groups, manages members and toggles modules | Each action asserted against the typed client |

## Acceptance criteria (class B unit level, §5.5.3)

- Data flow: enablement changes are read by the guard on the next request.
- Boundary: a user in several groups with conflicting enablement resolves to enabled.

## Notes

The frontend module list is cached and not invalidated after a change (PRB-015, TASK-144), so TC-005.3 verifies the action, not its immediate propagation.
