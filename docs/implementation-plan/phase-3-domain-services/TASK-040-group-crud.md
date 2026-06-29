# TASK-040 — Group CRUD

- **Phase:** 3 — Domain services
- **Software item / unit:** SI-GROUPS / U-GRP-Crud
- **Implements:** SR-014 (AC-1, AC-4); ADR-0005
- **Depends on:** TASK-027 (API deps / `AuthorizationService` guard, current-user DI) — must be merged first
- **Branch:** `feature/group-crud`
- **Status:** In Progress (audit 2026-06-29)

## Objective

Provide system-administrator-only creation and listing of user groups. Groups are the unit to which module enablement (TASK-042) and membership (TASK-041) attach, and the set of a user's groups feeds the module-access decision (TASK-043). This task delivers only group identity (create + list); membership and enablement are separate units. Traces to SR-014 AC-1 ("create and name a user group") and AC-4 ("the set of groups a user belongs to is retrievable").

## Interfaces to honor

Implements part of the `GroupService` contract from [12-interfaces.md](../../design/12-interfaces.md) §12.1 (provider SI-GROUPS):

```python
class GroupService:
    def create_group(self, actor: Account, name: str) -> Group: ...
    def list_groups(self) -> list[Group]: ...
    # membership(...), set_module_enabled(...), groups_of(...) land in TASK-041/042/043
```

- Every method authorizes via the injected `AuthorizationService` **before** mutating or returning data — deny-by-default (SR-005, §12.3 rule 1). Group management is restricted to `system administrator` (SR-014 control measure).
- This unit **must not** implement its own ad-hoc role check inline; it calls `AuthorizationService.authorize(actor, action, resource)` with action `groups:create` / `groups:list` and lets the policy engine decide (SR-005).
- Only `SI-PERSIST` touches PostgreSQL (§12.3 rule 3); the service uses the `GroupRepository`, never raw SQL.

## Implementation detail

- Files to create:
  - `backend/app/groups/service.py` — `GroupService` with `create_group`, `list_groups`.
  - `backend/app/db/models/group.py` — `Group` ORM model: `id` (UUID PK), `name` (unique, non-empty), `created_at`. (If a shared models module already exists, add the model there per existing convention — surgical, CLAUDE.md §3.)
  - `backend/app/db/repositories/group_repository.py` — `add(group)`, `list_all()`, `get_by_name(name)` (parameterized, SR-031.1).
  - `backend/app/db/alembic/versions/<rev>_create_groups.py` — Alembic migration creating `groups` (unique index on `name`).
- Endpoints (wired in SI-API; this task provides the service the routers call): `POST /groups`, `GET /groups` ([api-design.md](../../specifications/api-design.md) "Groups & module enablement — sysadmin only").
- Libraries: SQLAlchemy 2.x, Alembic, Pydantic v2 (request/response DTOs in `backend/app/api/schemas`).
- Audit (SR-023 AC-4 administrative action): `create_group` calls `AuditService.record(actor, "group.create", target=group.id, outcome="success", ip=...)`.
- Error cases (RFC 7807 `type` URIs, [api-design.md](../../specifications/api-design.md) error catalog):
  - Non-sysadmin caller → `403 /errors/forbidden` (no group data disclosed).
  - Missing/blank `name` → `400 /errors/validation-error` with field-level `errors[]`.
  - Duplicate group name → `409 /errors/conflict`.
- Edge cases: name is trimmed; empty-after-trim is a validation error; uniqueness is enforced both in Pydantic-independent DB constraint and surfaced as 409 (server-side validation authoritative, SR-031.5).

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/groups/test_group_service.py`):
  - sysadmin creates a named group → persisted and returned (SR-014 AC-1).
  - blank/whitespace name → validation error, nothing persisted (SR-014 AC-1).
  - duplicate name → conflict, single row remains (SR-014 AC-1).
  - non-sysadmin (doctor/admin/patient) `create_group` / `list_groups` → `authorize` denies, `403`, no data (SR-005 AC-2/AC-4, SR-014 control measure).
  - `list_groups` returns all created groups (SR-014 AC-4).
  - `create_group` emits a `group.create` audit event; deny path emits a denied-access audit event (SR-023 AC-4).
- Integration (`backend/tests/api/test_groups_api.py`): `POST /groups` then `GET /groups` round-trips through the router + authz dependency; non-sysadmin gets `problem+json` 403.

## Acceptance criteria

- [ ] A system administrator can create and name a group; it is persisted (SR-014 AC-1).
- [ ] Group names are unique; duplicates rejected with 409 (SR-014 AC-1).
- [ ] `GET /groups` returns the full group list to a sysadmin (SR-014 AC-4).
- [ ] All non-sysadmin callers are denied via `AuthorizationService` (deny-by-default, SR-005).
- [ ] Create and denied-access events are audited (SR-023).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit + integration tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (group endpoints)
- [ ] Audit events emitted for security-relevant actions (SR-023)
- [ ] Traceability matrix row updated (SR-014 → TASK-040 → tests)
- [ ] Security review N/A (no auth/session code; authz is consumed, not implemented here)

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-040a. Unchecked acceptance-criteria / DoD items above reflect the gaps the audit found; this task stays **In Progress** until they are addressed.
