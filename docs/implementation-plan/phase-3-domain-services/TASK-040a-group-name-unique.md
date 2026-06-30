# TASK-040a — Group name uniqueness DB constraint (remediation)

- **Phase:** 3 — Domain services
- **Implements / restores:** SR-014; remediates TASK-040 (and the auto-membership test gap in TASK-041)
- **Depends on:** TASK-040, TASK-041
- **Branch:** `feature/group-name-unique`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-040/041 verdict **PARTIAL**

## Objective

`Group.name` has no unique DB constraint — uniqueness relies on a TOCTOU `get_by_name` check, so two
concurrent creates can both insert. The AC requires a DB constraint. Also `sync_automatic_membership`
(TASK-041) has zero tests despite being the unit's primary requirement.

## Implementation detail

- Add `unique=True` on `Group.name` + an Alembic migration adding the unique index; map the IntegrityError
  to a 409.
- Add tests for `sync_automatic_membership`: auto-assign on activation, re-sync on user-type change, and
  confirm manual removal does not touch AUTO membership (note the PK design where AUTO/MANUAL cannot
  coexist — decide whether the model needs `source` in the PK).

## Acceptance criteria

- [x] Duplicate group names are rejected at the DB level (409), race-safe.
- [x] Auto-membership sync is covered by tests (assign + type-change re-sync).

## Definition of Done

- [x] Lint + type-check pass
- [x] Migration + tests pass
- [x] Traceability row updated (SR-014 → TASK-040a → tests)
- [x] Security review N/A
