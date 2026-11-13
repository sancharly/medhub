---
id: "TASK-220"
type: task
title: "Constant-query group membership lookup (characterisation first) and the remaining lookup indexes (migration 0012)"
status: draft
version: "1.1"
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
  - target: "PRB-021"
    relation: relates_to
  - target: "ADD-016"
    relation: relates_to
  - target: "SOUP-009"
    relation: relates_to
  - target: "TASK-219"
    relation: relates_to
tags: ["cr:CR-006", "performance", "migration", "control:protective"]
---

# TASK-220 — Constant-query group membership lookup (characterisation first) and the remaining lookup indexes (migration 0012)

- **Software item / unit:** SI-GROUPS `GroupService.groups_of` (ADD-009); group repository, models and
  Alembic `U-PER-Migrations` (ADD-016).
- **PRB:** PRB-024; PRB-021 (remaining part, CR-006 D-29). **CR:** CR-006 (change-analysis causes 4 and 5).
- **Depends on:** TASK-219 (approved; migration 0012 revises 0011). Otherwise parallel; no source file shared
  with TASK-227 (routers, `db/repositories/session.py`).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** M (`backend/app/groups/service.py`, `backend/app/db/repositories/group_repo.py`,
  `backend/app/db/models/{attachment,consent}.py`, new
  `backend/app/db/alembic/versions/0012_remaining_lookup_indexes.py`; tests
  `backend/tests/groups/test_groups_of.py`, `backend/tests/db/test_migration_0012_indexes.py`; records TS-005,
  TS-018). Two independent parts in one task by the human's decision (D-29); each part has its own tests and
  can be reviewed on its own.
- **Ask first:** applying 0012 to any existing database (it locks writes on `attachment` and `consent_grant`
  while the indexes build). The task runs it only on test databases.

## Objective

SR-026 AC 6: listing a user's groups issues a constant number of queries, independent of the number of
memberships. `groups_of` (`groups/service.py:131-138`) calls `self._group_repo.get(m.group_id)` once per
membership. RISK-004 control: the result set must not change (no enabled module newly denied; RISK-001: none
newly shown), so a characterisation test is written and committed **before** the rewrite.

SR-026 AC 6 (1.6, CR-006 D-29): listing a clinical entry's attachments and listing a doctor's patients by
active consent are served by an index. The TASK-219 QA review (finding 1) found that both lookups the code
issues still scan after migration 0011: `AttachmentRepository.list_for_clinical_entry`
(`attachment.clinical_entry_id`; called from `attachments/service.py:332`) and
`ConsentRepository.list_patients_for_doctor` (`consent_grant.doctor_id` and `active`; called from
`clinical/service.py:106`). The existing `ix_consent_grant_patient_doctor_active` leads with `patient_id` and
cannot serve a lookup by doctor. The three 0011 indexes that no current query uses stay (SR-026 AC 6; D-29).

## Implementation detail

1. **First commit-ready step:** `test_groups_of_characterisation` (SR-014 AC 4, SR-015 AC 3): accounts with 0,
   1, several MANUAL and AUTO memberships, a membership whose group was deleted (today skipped), duplicate
   group through two sources; assert the exact set and order of returned group ids. Green on the current code.
2. `GroupRepository.groups_for_account(account_id) -> list[Group]`: one `select(Group).join(GroupMembership)
   .where(GroupMembership.account_id == account_id)`; deduplicate and order as today (characterisation
   decides; document the order rule).
3. `groups_of` uses it; `memberships_for_account` stays for its other callers.
4. **Indexes (part 2, independent of steps 1 to 3):** `Index("ix_attachment_clinical_entry_id",
   "clinical_entry_id")` in `Attachment.__table_args__` and `Index("ix_consent_grant_doctor_id_active",
   "doctor_id", "active")` in `ConsentGrant.__table_args__`, next to the existing ones.
5. Migration `0012_remaining_lookup_indexes.py` (`down_revision = "0011"`): `op.create_index` × 2, `downgrade`
   drops them. Plain `CREATE INDEX`, as 0011 (single host, maintenance window; ADD-016). The deployment note
   (lock while building) goes to `infra/DEPLOY.md` and arc42 07 via TASK-225.
6. Model metadata and migration head agree (the existing `tests/db/test_migration.py` autogenerate-diff check).

## Tests (write first)

- `test_groups_of_characterisation` (SR-014 AC 4) unchanged before and after the rewrite.
- `test_groups_of_query_count_constant` (SR-026 AC 6): SQLAlchemy `before_cursor_execute` counter; queries for
  1, 10 and 100 memberships are equal.
- Existing module-enablement tests (SR-015 AC 3, AC 4) unchanged.
- `test_upgrade_downgrade_0012_empty_and_populated` (SR-026 AC 6): upgrade from 0011 on an empty database and
  on one seeded with 10 000 attachments and consent grants (several doctors, active and revoked grants);
  downgrade back to 0011; row counts unchanged.
- `test_remaining_lookups_use_index` (SR-026 AC 6): on the seeded database, after `ANALYZE` and with
  `enable_seqscan` left on, `EXPLAIN` of the two queries exactly as `AttachmentRepository.list_for_clinical_entry`
  and `ConsentRepository.list_patients_for_doctor` issue them (compiled from the repository statements, not a
  hand-written equivalent) names the new index and shows no `Seq Scan` on `attachment` or `consent_grant`.
- `test_without_the_0012_indexes_the_same_lookups_scan` (negative control): at revision 0011 the same two
  queries plan as `Seq Scan` on their table. Both lookups are checked, looping over the same query set as the
  positive test (TASK-219 QA finding 4).
- ORM drift: `tests/db/test_migration.py` passes at head, and at 0011 `compare_metadata` reports exactly the
  two `add_index` diffs (shows the drift test catches a missing 0012 index).
- Recorded in TS-005 (first CR-006 task to change it: 1.1 → 1.2, approval cleared; TC-005.x characterisation)
  and TS-018 (approved 1.2, so bumped with its approval cleared: TC-018.7 query count, TC-018.8 the 0012
  indexes; TC-018.4 to TC-018.6 are taken).

## Acceptance criteria

- [ ] SR-026 AC 6: constant queries at 1, 10, 100 memberships.
- [ ] SR-014 AC 4 / RISK-004: characterisation test identical before and after.
- [ ] SR-026 AC 6: the attachment-by-entry and patients-by-doctor lookups use the 0012 indexes (no sequential
  scan, seqscan enabled); both scan at 0011.
- [ ] Migration 0012 up and down on an empty and a populated database; ORM and migration head agree.
- [ ] 0012 not applied to any existing database without the human's go-ahead.

## Definition of Done

- [ ] `ruff`, `mypy`, backend suite green
- [ ] TS-005, TS-018 updated; ADD-009 consistent; ADD-016 confirmed for 0012 by TASK-225 (do not edit
  ADD-016 here: TASK-227 changes it concurrently)
- [ ] `traceability-check` no error for this record

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect) for PRB-024.
- 1.1 (2026-11-13) — CR-006 D-29 (human decision, TASK-219 QA finding 1; Software Architect role): migration
  0012 added to the scope (indexes on `attachment.clinical_entry_id` and `consent_grant(doctor_id, active)`),
  with upgrade/downgrade, `EXPLAIN`, negative-control and drift tests; `ask first` for existing databases;
  depends on TASK-219; size S → M; TS-018 ids corrected (TC-018.6 is taken); links to PRB-021, ADD-016,
  SOUP-009 and TASK-219 added. Stays `draft` (not started).
