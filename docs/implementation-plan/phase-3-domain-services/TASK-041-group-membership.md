# TASK-041 — Group membership (automatic + manual)

- **Phase:** 3 — Domain services
- **Software item / unit:** SI-GROUPS / U-GRP-Membership
- **Implements:** SR-014 (AC-2 auto-by-type, AC-3 manual add/remove, AC-4 retrievable), SR-004 (user type as membership input); ADR-0005
- **Depends on:** TASK-040 (Group CRUD) — must be merged first
- **Branch:** `feature/group-membership`
- **Status:** In Progress (audit 2026-06-29)

## Objective

Place users into groups two ways: **automatically by user type** (e.g. all doctors in a "Doctors" group) and **manually** by a system administrator adding/removing individuals. Expose `groups_of(account_id)` so the module-access guard (TASK-043) and `GET /me/modules` can compute enablement over the union of a user's groups. Traces to SR-014 AC-2/AC-3/AC-4 and uses the SR-004 user type as the automatic-membership key.

## Interfaces to honor

Extends `GroupService` from [12-interfaces.md](../../design/12-interfaces.md) §12.1:

```python
class GroupService:
    def add_member(self, actor: Account, group_id: UUID, account_id: UUID) -> None: ...     # manual (SR-014.3)
    def remove_member(self, actor: Account, group_id: UUID, account_id: UUID) -> None: ...   # manual (SR-014.3)
    def groups_of(self, account_id: UUID) -> list[Group]: ...                                # union: auto + manual (SR-014.4)
    # plus auto-binding hook below
```

- Manual add/remove is **sysadmin-only** via `AuthorizationService.authorize(actor, "groups:manage_members", group)` (SR-005, SR-014 control measure). `groups_of` is an internal read used by other items (SI-AUTHZ) and is **not** itself a privileged operation, but callers must already be authorized.
- This unit **must not** mutate user type or invent its own role logic; it reads `Account.user_type` (SR-004) as the automatic-membership input.
- Repositories only for persistence (§12.3 rule 3).

## Implementation detail

- Files to create / modify:
  - `backend/app/groups/service.py` — add `add_member`, `remove_member`, `groups_of`, and `sync_automatic_membership(account)` (recomputes type-derived memberships for one account).
  - `backend/app/groups/auto_membership.py` — mapping/strategy from `user_type` → automatic group(s). Keep it data-driven (a `GroupAutoRule` table or a typed mapping keyed by `Group.auto_user_type`), so adding an auto rule needs no code branch per type.
  - `backend/app/db/models/group.py` — add nullable `auto_user_type` column to `Group` (a group is either auto-bound to one user type or manual-only).
  - `backend/app/db/models/group_membership.py` — `GroupMembership` join model: `group_id`, `account_id`, `source` (`AUTO` | `MANUAL`), `created_at`; unique `(group_id, account_id)`.
  - `backend/app/db/repositories/group_repository.py` — `add_membership`, `remove_membership`, `memberships_for_account`, `members_of_group`.
  - `backend/app/db/alembic/versions/<rev>_group_membership.py` — migration: `group_membership` table + `groups.auto_user_type`.
- Automatic-membership trigger points: call `sync_automatic_membership` on account **activation** and on **user-type change** (SI-IDENTITY hooks; wire via the existing identity service call sites — surgical). New accounts with a matching type land in the auto group without manual action (SR-014 AC-2).
- Endpoints (SI-API): `POST /groups/{id}/members`, `DELETE /groups/{id}/members/{accountId}` ([api-design.md](../../specifications/api-design.md)).
- Audit (SR-023 AC-4): `add_member` / `remove_member` record `group.member.add` / `group.member.remove` with actor, target account, group id.
- Error cases:
  - Non-sysadmin manual add/remove → `403 /errors/forbidden`.
  - Unknown group or account → `404 /errors/not-found`.
  - Adding an existing member → idempotent success (no duplicate row) or `409 /errors/conflict` — choose idempotent; document in OpenAPI.
- Edge cases: manually removing a member whose membership is `AUTO` must not silently fail — manual removal targets only `MANUAL` rows; automatic rows are managed solely by `sync_automatic_membership` (prevents a sysadmin removal being undone, and an auto member from being orphaned). A user belongs to a group if **any** membership row exists (AUTO or MANUAL); `groups_of` returns the de-duplicated union (SR-014 AC-4).

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/groups/test_membership.py`):
  - account of a given type → `sync_automatic_membership` adds it to the matching auto group (SR-014 AC-2, SR-004).
  - user-type change re-syncs: removed from old auto group, added to new (SR-014 AC-2).
  - sysadmin manual add then `groups_of` includes the group (SR-014 AC-3/AC-4).
  - sysadmin manual remove drops the `MANUAL` membership; an `AUTO` membership for the same group is untouched (SR-014 AC-3 edge).
  - `groups_of` returns the de-duplicated union of AUTO + MANUAL (SR-014 AC-4).
  - non-sysadmin add/remove → denied 403, no change, denied-access audited (SR-005, SR-023).
  - add/remove emit membership audit events (SR-023 AC-4).
- Integration (`backend/tests/api/test_group_members_api.py`): member add/remove via routers; non-sysadmin denied with `problem+json`.

## Acceptance criteria

- [ ] Users are auto-assigned to a group by user type on activation and on type change (SR-014 AC-2).
- [ ] A sysadmin can manually add and remove a user from a group (SR-014 AC-3).
- [ ] Manual removal affects only manual memberships; automatic ones are managed by the sync (SR-014 AC-3).
- [ ] `groups_of(account_id)` returns the union of a user's groups for access decisions (SR-014 AC-4).
- [ ] Membership changes restricted to sysadmin and audited (SR-005, SR-023).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit + integration tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (membership endpoints)
- [ ] Audit events emitted for security-relevant actions (SR-023)
- [ ] Traceability matrix row updated (SR-014, SR-004 → TASK-041 → tests)
- [ ] Security review N/A (authz consumed, not implemented here)

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-040a. Unchecked acceptance-criteria / DoD items above reflect the gaps the audit found; this task stays **In Progress** until they are addressed.
