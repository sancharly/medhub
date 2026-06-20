# TASK-043 — ModuleAccessGuard

- **Phase:** 3 — Domain services
- **Software item / unit:** SI-AUTHZ / U-AUTHZ-ModuleGuard
- **Implements:** SR-015 (AC-3 access only if enabled for a group, AC-4 disabling removes access); ADR-0005
- **Depends on:** TASK-042 (per-group module enablement) — must be merged first
- **Branch:** `feature/module-access-guard`
- **Status:** Not started

## Objective

Provide the runtime check that decides whether a given account may access a given module: enabled for **at least one** of the account's groups (union). This is the gate `GET /me/modules` reads and that every module endpoint passes **before** the consent/authorization check. Disabling a module for all of a user's groups immediately removes access because the guard reads live enablement on each request. Traces to SR-015 AC-3/AC-4.

## Interfaces to honor

Implements `ModuleAccessGuard` from [12-interfaces.md](../../design/12-interfaces.md) §12.1 (provider SI-AUTHZ; consumers SI-MODHOST, SI-API) **verbatim**:

```python
class ModuleAccessGuard:
    def is_module_enabled(self, account_id: UUID, module_key: str) -> bool: ...
```

- Returns `True` iff `module_key` is enabled for **any** group in `groups_of(account_id)` — union semantics (SR-015 AC-3). Reads live (no caching that could mask a disable, SR-015 AC-4).
- This is a pure decision function: it **must not** itself raise an HTTP error or write audit. The FastAPI dependency wrapper (SI-API) and the module router mount (TASK-072) translate a `False` result into `403 /errors/forbidden` and the denied-access audit event. Keeping the guard side-effect-free keeps it independently unit-testable.
- It composes with, but is distinct from, `AuthorizationService.authorize(...)`: module endpoints pass the guard (enablement) **then** authorization (consent) per [api-design.md](../../specifications/api-design.md) "Authentication & authorization flow" step 3 and runtime view 6.4.

## Implementation detail

- Files to create:
  - `backend/app/authz/module_guard.py` — `ModuleAccessGuard` consuming `GroupService.groups_of` (TASK-041) and `GroupRepository.enabled_module_keys_for_groups` (TASK-042).
  - `backend/app/api/deps.py` — add a FastAPI dependency `require_module_enabled(module_key)` that resolves the current account, calls `is_module_enabled`, and on `False` raises the `forbidden` problem and emits the denied-access audit event (the side-effecting wrapper). (Modify the existing deps module — surgical.)
- Implementation: fetch the account's group ids once, query `enabled_module_keys_for_groups(group_ids)` (single parameterized query), test membership of `module_key`. No N+1.
- Audit: the denied-module-access event (SR-023) is emitted by the dependency wrapper, not the guard.
- Error cases (raised by the wrapper, not the guard): not enabled → `403 /errors/forbidden`; no protected data disclosed (SR-005 AC-4).
- Edge cases: account in zero groups → always `False`. Module enabled in one of several groups → `True` (union, SR-015 AC-3). Module disabled in the only group that had it → `False` on the very next call (SR-015 AC-4, live read). Unknown `module_key` → `False` (deny-by-default).

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/authz/test_module_guard.py`):
  - account in a group with the module enabled → `True` (SR-015 AC-3).
  - account in two groups, module enabled in only one → `True` (union, SR-015 AC-3).
  - account in groups, module enabled in none → `False` (deny-by-default).
  - module disabled (set `enabled=false` in TASK-042) for the only group that had it → `is_module_enabled` returns `False` on the next call (SR-015 AC-4, live read).
  - account in zero groups → `False`.
  - unknown `module_key` → `False`.
- Integration (`backend/tests/api/test_module_guard_dep.py`): a route protected by `require_module_enabled("dicom-viewer")` returns `403 problem+json` when not enabled and emits a denied-access audit event; passes through when enabled (SR-015 AC-3/AC-4, SR-023).

## Acceptance criteria

- [ ] `is_module_enabled` returns true iff the module is enabled for at least one of the account's groups (SR-015 AC-3, union).
- [ ] When the module is disabled for all of the user's groups, the guard returns false on the next request (SR-015 AC-4, live read — no stale cache).
- [ ] The guard is side-effect-free; HTTP 403 + denied-access audit are produced by the API dependency wrapper (SR-005, SR-023).
- [ ] Unknown module / no-group account denied by default.

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit + integration tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (N/A — internal guard; dependency surfaced where mounted)
- [ ] Audit events emitted for security-relevant actions (denied module access, SR-023)
- [ ] Traceability matrix row updated (SR-015 → TASK-043 → tests)
- [ ] Security review completed (authorization code — SR-031.6)
