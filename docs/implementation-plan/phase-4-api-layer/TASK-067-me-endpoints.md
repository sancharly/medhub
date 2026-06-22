# TASK-067 — Current-user (`/me`) endpoints

- **Phase:** 4 — API layer
- **Software item / unit:** SI-API / U-API-Routers, U-API-DTO
- **Implements:** SR-003 (authenticated user views their own profile; data-minimized);
  SR-015 (modules enabled for the user's groups, the gate the SPA reads for nav)
- **Depends on:** TASK-030 (AccountService read), TASK-043 (ModuleAccessGuard / module enablement
  resolution) — must be merged first
- **Branch:** `feature/me-endpoints`
- **Status:** COMMITTED on `feature/phase-4` (commit ae0f5ff)

## Objective

Expose the current-user HTTP surface: `GET /me` returns the authenticated user's own profile
(data-minimized, scoped strictly to the caller — SR-003), and `GET /me/modules` returns the set of
module keys enabled for at least one group the user belongs to (SR-015.3, SR-016.2). The SPA shell
and module registry read `GET /me/modules` to decide which nav items to render
([12-interfaces.md](../../design/12-interfaces.md) §12.2). Traces to SR-003, SR-015.

## Interfaces to honor

HTTP contract (verbatim from [api-design.md](../../specifications/api-design.md)):

| Method & path     | Purpose                                | Key reqs         |
|-------------------|----------------------------------------|------------------|
| `GET /me`         | current user profile                   | SR-003           |
| `GET /me/modules` | modules enabled for the user's groups  | SR-015, SR-016.2 |

Consumes ([12-interfaces.md](../../design/12-interfaces.md) §12.1) **verbatim**:

```python
# get_current_user (TASK-025) yields the Account; profile is projected from it
GroupService.groups_of(self, account_id: UUID) -> list[Group]                 # TASK-040/043
ModuleAccessGuard.is_module_enabled(self, account_id: UUID, module_key: str) -> bool  # TASK-043
```

Both endpoints declare the `require(action, resource_loader)` guard (TASK-025); the resource is the
caller themselves — `GET /me` is authorized only for the authenticated user's own record (SR-003.3).
`GET /me/modules` is the **server-authoritative** module gate the SPA reads; the SPA only hides nav,
never enforces access (SR-031.5, ADR-0003).

Must **not**: return another user's profile or accept an id parameter — `/me` is strictly the
session subject (SR-003.2/3); return clinical fields in the profile projection (data-minimization,
SR-003, SR-009 spirit); list modules merely installed but not enabled for the user's groups (that is
`GET /modules`, TASK-063) — `/me/modules` is the per-user enabled set (SR-015.3).

## Implementation detail

- Files to create:
  - `backend/app/api/routers/me.py` — `APIRouter(prefix="/me")` with `GET /me` and `GET /me/modules`;
    mounted under `/api/v1`. (The `GET /me/consents` endpoint is owned by TASK-064.)
  - `backend/app/api/schemas/me.py` — Pydantic v2 DTOs (camelCase):
    - `MeResponse { id, firstName, surname, email, accountType }` (profile, data-minimized — SR-003)
    - `MeModulesResponse { moduleKeys: list[str] }` (the enabled set the SPA gates nav on)
    - `MeSummary { id, firstName, surname, accountType }` (compact projection reused by
      `LoginResponse` in TASK-060)
- `GET /me` (authenticated): authorize `profile:read_own`; project the current user's own fields into
  `MeResponse`; 200. No id parameter; the subject is always the session user (SR-003.2/3).
- `GET /me/modules` (authenticated): resolve the user's groups (`groups_of`) and the modules enabled
  for any of them via `ModuleAccessGuard.is_module_enabled` across the installed registry; return the
  enabled `moduleKeys` (SR-015.3, SR-016.2). When a module is disabled for all of the user's groups it
  is absent (SR-015.4). 200 `MeModulesResponse`.
- Edge cases: a user in no group, or with no enabled modules → `moduleKeys: []`; enabling/disabling a
  module for a group (TASK-063) changes this set on the next call (the SPA refetches via TanStack
  Query, TASK-080/082).
- Error cases (RFC 7807, base `https://medhub.example/errors/`): no/invalid session →
  `401 /errors/unauthenticated` (generic, via TASK-025); these are read-only GETs so no CSRF applies.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/api/test_me_router.py`):
  - authenticated user → `GET /me` returns **their own** profile, data-minimized (no clinical
    fields), no id parameter accepted (SR-003.2/3).
  - unauthenticated `GET /me` → 401 (SR-002.3, deny-by-default).
  - `GET /me/modules` returns exactly the modules enabled for the user's groups; a module disabled
    for all their groups is absent (SR-015.3/4, SR-016.2).
  - a user in no group → `moduleKeys: []`.
- Integration (`backend/tests/api/test_me_integration.py`): enable a module for the user's group via
  TASK-063 → `GET /me/modules` now includes it; disable → it disappears (SR-015, cross-task).

## Acceptance criteria

- [ ] An authenticated user can view their own profile (SR-003.2).
- [ ] A user cannot view another user's profile via `/me`; no id parameter is honored (SR-003.3).
- [ ] The profile projection is data-minimized (no clinical fields).
- [ ] `GET /me/modules` returns the modules enabled for the user's groups (SR-015.3, SR-016.2).
- [ ] A module disabled for all of the user's groups is absent from the list (SR-015.4).
- [ ] Both endpoints require an authenticated session (SR-002.3, deny-by-default SR-005).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit + integration tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (two endpoints + DTOs)
- [ ] Audit events emitted for security-relevant actions (N/A — own-profile read; clinical reads audited elsewhere)
- [ ] Traceability matrix row updated (SR-003, SR-015 → TASK-067 → tests)
- [ ] Security review N/A (authz consumed, not implemented here)
