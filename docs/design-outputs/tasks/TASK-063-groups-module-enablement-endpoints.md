---
id: "TASK-063"
type: task
title: "Groups & module-enablement endpoints"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-014"
    relation: implements
  - target: "SR-015"
    relation: implements
  - target: "SR-016"
    relation: implements
  - target: "TASK-040"
    relation: relates_to
  - target: "TASK-041"
    relation: relates_to
  - target: "TASK-042"
    relation: relates_to
tags: ["phase:4-api-layer"]
---

- **Phase:** 4 — API layer
- **Software item / unit:** SI-API / U-API-Routers, U-API-DTO
- **Implements:** SR-014 (group create/list, manual membership); SR-015 (per-group module
  enable/disable); SR-016 (installed-module registry listing)
- **Depends on:** TASK-040 (GroupService create/list), TASK-041 (membership), TASK-042 (module
  enablement) — must be merged first
- **Branch:** `feature/groups-modules-endpoints`
- **Status:** Completed

## Objective

Expose the SI-GROUPS HTTP surface restricted to system administrators: group create/list
(`POST /groups`, `GET /groups`), manual membership (`POST /groups/{id}/members`,
`DELETE /groups/{id}/members/{accountId}`), per-group module enablement
(`PUT /groups/{id}/modules/{moduleKey}`), and the installed-module registry listing (`GET /modules`).
Routers delegate to `GroupService`; enablement is the input the runtime `ModuleAccessGuard` (SR-015)
and `GET /me/modules` (TASK-067) read. Traces to SR-014, SR-015, SR-016.

## Interfaces to honor

HTTP contract (verbatim from [api-design.md](../../specifications/api-design.md)):

| Method & path                                          | Purpose                          | Key reqs |
|--------------------------------------------------------|----------------------------------|----------|
| `POST /groups`                                         | create a named group             | SR-014.1 |
| `GET /groups`                                          | list groups                      | SR-014   |
| `POST /groups/{id}/members`                            | manual add member                | SR-014.3 |
| `DELETE /groups/{id}/members/{accountId}`              | manual remove member             | SR-014.3 |
| `PUT /groups/{id}/modules/{moduleKey}`                 | enable/disable module for group  | SR-015   |
| `GET /modules`                                         | installed module registry        | SR-016   |

Consumes ([12-interfaces.md](../../design/12-interfaces.md) §12.1) **verbatim**:

```python
GroupService.create_group(self, name: str) -> Group                                    # TASK-040
GroupService.membership(self, group_id: UUID, account_id: UUID, add: bool) -> None     # TASK-041
GroupService.set_module_enabled(self, group_id: UUID, module_key: str, enabled: bool)  # TASK-042
# installed-module registry comes from SI-MODHOST discovery (TASK-070); GET /modules reads it
```

All endpoints declare the `require(action, resource_loader)` guard (TASK-025); only **sysadmin** is
authorized (SR-014/015 — group/module administration). `GET /modules` lists the installed registry
(from SI-MODHOST `U-MH-Discovery`), independent of per-user enablement (which is `GET /me/modules`).

Must **not**: re-implement membership or enablement logic (delegate to SI-GROUPS); auto-derive
type-based membership here (that is `U-GRP-Membership`/TASK-041 server logic, not an endpoint, SR-014.2);
grant module access from this endpoint — enablement is the **input** to the runtime guard, not the
access decision itself (SR-005, SR-015).

## Implementation detail

- Files to create:
  - `backend/app/api/routers/groups.py` — `APIRouter(prefix="/groups")` (create/list/members/modules)
    + `APIRouter(prefix="/modules")` `GET` listing; mounted under `/api/v1`.
  - `backend/app/api/schemas/group.py` — Pydantic v2 DTOs (camelCase):
    - `GroupCreateRequest { name: str }`
    - `GroupResponse { id, name, autoMembershipType: AccountType | None }`
    - `GroupListResponse { items: list[GroupResponse], nextCursor: str | None }` (paginated)
    - `MemberAddRequest { accountId: UUID }`
    - `ModuleEnablementRequest { enabled: bool }` (PUT body)
    - `ModuleResponse { moduleKey, name, version, requiredPermissions: list[str] }` (mirrors
      `ModuleManifest`, api-design.md)
    - `ModuleListResponse { items: list[ModuleResponse] }`
- `POST /groups` (sysadmin): authorize `group:create`; `GroupService.create_group(name)`; 201
  `GroupResponse`. Audit `GROUP_CREATE`.
- `GET /groups` (sysadmin): authorize `group:list`; paginated, access-scoped (SR-014.4 — membership
  retrievable for module decisions).
- `POST /groups/{id}/members` (sysadmin): authorize `group:manage_members`;
  `GroupService.membership(id, accountId, add=True)`; 204. Absent group/account → 404. Audit.
- `DELETE /groups/{id}/members/{accountId}` (sysadmin): authorize `group:manage_members`;
  `membership(id, accountId, add=False)`; 204 (idempotent). Audit.
- `PUT /groups/{id}/modules/{moduleKey}` (sysadmin): authorize `group:set_module`;
  `set_module_enabled(id, moduleKey, body.enabled)`; idempotent upsert; 200. Enabling for an unknown
  `moduleKey` (not in the installed registry) → 404. Audit `MODULE_ENABLEMENT_CHANGE` with group,
  module, enabled flag (SR-015.1/2, SR-023).
- `GET /modules` (sysadmin): list the installed-module registry from SI-MODHOST (SR-016) — each
  manifest's key/name/version/required permissions; 200 `ModuleListResponse`.
- Error cases (RFC 7807, base `https://medhub.example/errors/`): missing `name`/`accountId`/`enabled`
  → `400 /errors/validation-error`; non-sysadmin caller → `403 /errors/forbidden`; absent
  group/account/module → `404 /errors/not-found`.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/api/test_groups_router.py`):
  - sysadmin creates a named group → 201 (SR-014.1).
  - `GET /groups` lists groups, paginated; membership is retrievable for module decisions (SR-014.4).
  - manual add then remove a member → 204 each; remove is idempotent (SR-014.3).
  - `PUT .../modules/{key}` enable then disable → 200 each, enablement persisted (SR-015.1/2).
  - enabling an unknown moduleKey → 404 (only installed modules can be enabled).
  - non-sysadmin caller on any endpoint → 403 (SR-014/015 administration).
  - module-enablement changes audited (SR-023).
- Unit (`backend/tests/api/test_modules_listing.py`): `GET /modules` returns the installed registry
  (key/name/version/permissions) from SI-MODHOST (SR-016); reflects exactly the discovered manifests.
- Integration (`backend/tests/api/test_group_module_integration.py`): create group → enable a module
  → assert the member's `GET /me/modules` (TASK-067) now includes it (cross-task, SR-015.3).

## Acceptance criteria

- [x] Sysadmin can create and name a group (SR-014.1).
- [x] Group membership is retrievable for module-access decisions (SR-014.4).
- [x] Sysadmin can manually add/remove a member (SR-014.3).
- [x] Sysadmin can enable/disable a module per group; only installed modules are enablable (SR-015.1/2).
- [x] `GET /modules` lists the installed module registry (SR-016).
- [x] All endpoints are sysadmin-only and authorized server-side (SR-005); enablement changes audited (SR-023).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit + integration tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (six endpoints + DTOs)
- [x] Audit events emitted for security-relevant actions (group create, membership, enablement — SR-023)
- [x] Traceability matrix row updated (SR-014, SR-015, SR-016 → TASK-063 → tests)
- [x] Security review N/A (authz consumed, not implemented here)

## Audit verdict (2026-06-29)

- **Verdict:** FAIL (CSRF enforcement missing — resolved by TASK-069a)
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-069a completed. All AC/DoD items now satisfied.

## QA sign-off

- **Date:** 2026-06-30
- **Reviewer:** QA Engineer agent (phase-4 audit remediation)
- **Evidence:** CSRF gap closed by TASK-069a; OpenAPI regenerated in TASK-068a; 484 tests pass (ruff + mypy clean).
