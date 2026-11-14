---
id: TS-005
type: test-specification
title: Groups and per-group module enablement verification
status: approved
version: "1.4"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-14"
links:
  - target: SR-014
    relation: verifies
  - target: SR-015
    relation: verifies
tags:
  - level:unit
  - class:B
---

# TS-005 — Groups and per-group module enablement verification

## Scope

Software requirements covered: SR-014, SR-015.
Software items under test: SI-GROUPS, SI-AUTHZ, SI-FE-CORE, SI-FE-MODREG.
Levels: unit, integration.

## Preconditions and environment

Build: branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 24 LTS (build stage node:24.22.2-trixie-slim; CI node-version 24) with `frontend/package-lock.json`.
Unit and service tests run with no external services (in-memory repositories). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-005.1 | SR-014 | `backend/tests/groups/test_group_service.py`, `backend/tests/groups/test_membership.py`, `backend/tests/api/test_groups_router.py` | Group CRUD works; membership is assigned automatically by user type and manually | Name uniqueness enforced; both membership paths covered |
| TC-005.2 | SR-015 | `backend/tests/groups/test_module_enablement.py`, `backend/tests/authz/test_module_guard.py`, `backend/tests/modules/test_module_gating.py` | A module is reachable only for groups where it is enabled | Disabled group receives a denial, not an empty success |
| TC-005.3 | SR-014, SR-015 | `frontend/src/core/admin/groups/GroupsPage.test.tsx` | The admin UI creates groups, manages members and toggles modules | Each action asserted against the typed client |
| TC-005.4 | SR-014 (AC 4), SR-026 AC 6 | `backend/tests/groups/test_groups_of.py` (real DB): `test_groups_of_characterisation`, `test_groups_of_lists_a_group_once_per_account`, `test_groups_of_skips_a_membership_whose_group_is_missing`, `test_groups_of_query_count_constant` (the PRB-024 case), `test_module_gate_query_count_constant` (module gating: `ModuleAccessGuard.is_module_enabled` and the two repository calls of `GET /me/modules`), (TASK-220, RISK-004) | `GroupService.groups_of` returns the same set of groups before and after the single-query rewrite for 0, 1 and several AUTO and MANUAL memberships, a group once per account, a membership without a group row skipped; the query count of `groups_of` and of the module-gating paths is equal for 1, 10 and 100 memberships. Order is unspecified (no ORDER BY) and compared sorted | All listed tests pass; the characterisation tests were green on the per-membership implementation (`c69d7dc`) and `test_groups_of_query_count_constant` failed there with `{1: 3, 10: 12, 100: 102}`; the module-gating test passes on it (constant 3 queries) and fails with a planted N+1 |
| TC-005.5 | SR-015 (AC 5) | `frontend/src/modules/useMyModules.test.tsx`: `module disabled elsewhere disappears within 60 s`, `module enabled elsewhere appears within 60 s`, `remount (next navigation) refetches`, `failed refetch keeps the last known modules`, `the change shows within 60 s when the server and the network are slow` (1 s MSW delay, change right after the server read), `a failed refetch leaves the cached list in place`, `admin module mutation invalidates myModules`, `admin add-member mutation invalidates myModules`, `admin remove-member mutation invalidates myModules`, `only useMyModules calls apiClient.listMyModules()`, `only queryKeys.ts spells the myModules key` (TASK-221, RISK-004) | A change of a module's enablement made by someone else reaches the viewer link of `AttachmentItem` within 60 s (interval refetch every 50 s) or on the next mount, without a reload; a failed refetch keeps the last known list; the administrator's own mutations (module toggle, member add or remove) invalidate the list; one hook and one key spelling serve every module-dependent reader | All listed tests pass; each fails when its mechanism is removed by hand (a 60 s interval: 4 fail; no `refetchInterval`: 4 fail; the `!isError &&` mutant of `AttachmentItem`: the failed-refetch test fails; no `refetchOnMount`: remount fails; the query function swallowing an error into `[]`: 2 fail; no invalidation in `GroupModules`, in the add-member or in the remove-member path: 1 fails each; the key spelled inline: the key test fails) |

## Acceptance criteria (class B unit level, §5.5.3)

- Data flow: enablement changes are read by the guard on the next request.
- Boundary: a user in several groups with conflicting enablement resolves to enabled.

## Notes

TC-005.3 verifies the admin action; its propagation to other users' UI is verified by TC-005.5 (PRB-015, TASK-221).

## Version history

- 1.1 (2026-10-30): approved (self-approved).
- 1.2 (2026-11-14): TASK-220. Added TC-005.4 (`groups_of` characterisation and constant query count); `test_membership.py::test_groups_of_returns_groups_for_all_memberships` now stubs `groups_for_account` (TC-005.1). Content change, so the approval record is removed. `in_review`.
- 1.2 (2026-11-14, round 2): TC-005.4 lists `test_module_gate_query_count_constant`; stub test asserts the repository call. Still `in_review`.
- 1.2 (2026-11-14): QA review of TASK-220 (round 2): `approved` (status only; content unchanged).
- 1.3 (2026-11-14): TASK-221. Added TC-005.5 (module refresh within 60 s, on remount, kept on failure, invalidation by admin mutations) and rewrote the note on PRB-015. Content change, so the approval is removed. `in_review`.
- 1.4 (2026-11-14): TASK-221 round 2. Interval 50 s, latency test, stronger failed-refetch test, add-member test; TC-005.5 lists them. Still `in_review`.
- 1.4 (2026-11-14) — QA review of TASK-221 (round 2): `approved` (status only; content unchanged).
