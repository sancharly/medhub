---
id: "TASK-220"
type: task
title: "Constant-query group membership lookup (characterisation first) and the remaining lookup indexes (migration 0012)"
status: approved
version: "1.5"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-14"
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

- [x] SR-026 AC 6: constant queries at 1, 10, 100 memberships.
- [x] SR-014 AC 4 / RISK-004: characterisation test identical before and after.
- [x] SR-026 AC 6: the attachment-by-entry and patients-by-doctor lookups use the 0012 indexes (no sequential
  scan, seqscan enabled); both scan at 0011.
- [x] Migration 0012 up and down on an empty and a populated database; ORM and migration head agree.
- [x] 0012 not applied to any existing database without the human's go-ahead.

## Definition of Done

- [x] `ruff`, `mypy`, backend suite green
- [x] TS-005, TS-018 updated; ADD-009 consistent; ADD-016 confirmed for 0012 by TASK-225 (do not edit
  ADD-016 here: TASK-227 changes it concurrently)
- [x] `traceability-check` no error for this record

## QA review round 1 (qa-engineer, 2026-11-14) — CHANGES REQUESTED

The code is correct and the suite is green. The changes requested are about what the evidence proves and about
the PRB-024 record.

1. **HIGH: TC-018.7 checks a function that no request path calls, so SR-026 AC 6 "listing a user's groups" is
   not verified on the paths the AC names.** `GroupService.groups_of` has no caller in `backend/app/` or
   `backend/modules/` (grep: only its definition, `groups/service.py:134`). Module gating resolves
   memberships elsewhere: `ModuleAccessGuard.is_module_enabled` (`authz/module_guard.py:16-27`, called from
   `api/deps.py:179` for every module route) and `GET /me/modules` (`api/routers/me.py:33-35`). Both use
   `memberships_for_account` plus `enabled_module_keys_for_groups`, which is already a constant number of
   queries. A QA probe on PostgreSQL measured `is_module_enabled` at `{1: 3, 10: 3, 100: 3}`. No regression
   test covers that path, so a future N+1 in the guard would pass TC-018.7. SR-026 AC 6 says "data-access
   paths used by authorization and module gating", and those paths are not the one under test.
   → Add `test_module_gate_query_count_constant` to `backend/tests/groups/test_groups_of.py`. It should count
   `ModuleAccessGuard(GroupRepository(s), ModuleRepository(s)).is_module_enabled(acct.id, key)` at 1, 10 and
   100 memberships with the same `before_cursor_execute` counter and `expire_all()`, and assert that the
   counts are equal. Cover the `/me/modules` pair too (call it through the router or assert the same two repo
   calls). List the test in TS-018 TC-018.7 and TS-005 TC-005.4 as the module-gating case. Keep the
   `groups_of` test as the PRB-024 case.
2. **MEDIUM: PRB-024 is not updated, and the path its Impact names is not the module-gating path.**
   `docs/problem-reports/PRB-024-*.md` 1.0 says "Latency grows with membership count on a path used by
   module gating", and its Resolution still reads "Not yet tracked by a task". It cannot move to `resolved`
   as written (problem-report-resolution: Resolution names the change and its verification).
   → PRB-024 1.1 (Software Developer):
   - Correct the Observed and Impact sections: `groups_of` is unused. The cost was latent, with no request path
     affected, and module gating already used a constant number of queries (finding 1).
   - Add an `## Investigation` section with the `file:line` references above.
   - Write a Resolution that names TASK-220: `group_repo.py:54-61` `groups_for_account`, `service.py:134-136`,
     and the tests with their negative control on `c69d7dc`, `{1: 3, 10: 12, 100: 102}`.
   - Leave the status `open` for QA to move to `resolved`.
   If the human prefers, PRB-024 could instead be reworded so that its criticality and safety evaluation say
   "latent". Either way, the record must not say a hot path was fixed.
3. **LOW: the unit test stub is now a pass-through.**
   `backend/tests/groups/test_membership.py:113-124` asserts only `len(result) == 2`.
   → Also assert `mock_group_repo.groups_for_account.assert_called_once_with(account_id)` and
   `result == [g1, g2]`. The real-database TC-005.4 carries the behaviour, so this is LOW.
4. **LOW: TC-018.8 does not say why `account` is allowed a `Seq Scan`.**
   `test_remaining_lookups_use_index` asserts no `Seq Scan` only on `attachment`/`consent_grant`, and the plan
   for the doctor lookup still has `Seq Scan on account`. QA probe results: at 10 000 accounts the planner
   hash-joins 150 of the 10 000 rows, a small-table choice. At 210 000 accounts it switches to
   `Index Scan using account_pkey` (merge join). The join is therefore index-servable and the assertion
   scope is acceptable.
   → Add one sentence to TC-018.8: the `account` side is joined by primary key, and a seq scan there is a
   planner choice at seed size.

Checked and accepted:
- Characterisation: the four new tests run on HEAD `03b1400` (the per-membership `groups_of`). The three
  characterisation tests pass, and the query-count test fails with `{1: 3, 10: 12, 100: 102}`, which
  reproduces the developer's claim.
- Positive index test without 0012: a QA mutant ran the positive test body with the upgrade removed. For both
  lookups the index name is absent and `Seq Scan on <table>` is present, so both of its assertions are
  discriminating. The negative control covers it.
- 0012 upgrade/downgrade, drift test, and `ix_consent_grant_doctor_id_active` used as `Bitmap Index Scan`
  with `Index Cond (doctor_id, active = true)`.
- PRB-021 stays `open` as its own Resolution requires: it waits for the TASK-226 query-plan record, which
  this review cannot replace.

Verification run (2026-11-14):
- `uv run pytest -q`: 1661 passed, 10 skipped.
- `modules/dicom_viewer/tests`: 31 passed.
- `ruff check .`: clean. `ruff format --check` on the 8 changed files: clean.
- `mypy app`: 136 files, no issues.
- `python3 -m unittest discover -s infra/tests`: 178 OK.
- traceability scope TASK-220, TS-005, TS-018, PRB-021, PRB-024, PRB-082, SR-026 (39 records): 0 errors,
  2 W5 warnings. TASK-136 and TP-001, both `approved`, link the `in_review` TS-018 and TS-005; this is
  expected while these are under review.

## QA review round 2 (qa-engineer, 2026-11-14) — APPROVED

The four round-1 findings and the PRB-082 line references were checked again:

1. **HIGH, fixed.** `test_module_gate_query_count_constant` counts `is_module_enabled` and the `/me/modules`
   repository pair at 1, 10 and 100 memberships. In a QA mutant, a scratch copy with a per-membership
   `GroupRepository.get` planted in `module_guard.py` failed with `{1: 4, 10: 13, 100: 103}`. The working-tree
   `module_guard.py` has no diff.
2. **MEDIUM, fixed.** PRB-024 1.1 now describes a latent cost, with Investigation and Resolution sections and
   the correct `file:line` references.
3. **LOW, fixed.** The stub test asserts `assert_called_once_with(account_id)` and `result == [g1, g2]`.
4. **LOW, fixed.** TC-018.8 has the note on the `account` seq scan.
5. **PRB-082 references verified against the code:**
   - `service.py:187-190` is the pass-2 `get_object_stream` call.
   - `service.py:197-204` is the SUCCESS audit row.
   - `service.py:206-232` and `230-232` are still correct.
   - `attachments.py:109-116` and `117-119` are still correct.

Remaining LOWs (not blocking):
- The `/me/modules` case calls the same two repository methods as `me.py:33-35` through a copy in the
  test, not through the router. A change to the router alone would not be caught. Calling `get_my_modules`
  directly with the session would close this.
- TS-005 (1.2) and TS-018 (1.3) changed content in round 2 without a version bump. Both were unapproved
  and `in_review`, and their version histories record the change.

The local `infra-postgres-1` is still at revision 0010, so 0012 was not applied to an existing database.

Verification run (2026-11-14):
- `uv run pytest -q`: 1662 passed, 10 skipped.
- `modules/dicom_viewer/tests`: 31 passed.
- `ruff check .`: clean. `ruff format --check` on the 8 files: clean.
- `mypy app`: 136 files, no issues.
- `infra/tests`: 178 OK.
- traceability scope TASK-220, TS-005, TS-018, PRB-021, PRB-024, PRB-082, SR-026 (39 records): 0 errors,
  2 W5 warnings. TASK-136 and TP-001, both `approved`, link TS-018 and TS-005, which were still `in_review`
  when the check ran; these are resolved by this approval.

Status changes: TASK-220, TS-005 and TS-018 move `in_review → approved`, and PRB-024 moves `open → resolved`
(CR-006 holds the `resolves` link). PRB-021 stays `open`: its Resolution waits for TASK-226.

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect) for PRB-024.
- 1.1 (2026-11-13) — CR-006 D-29 (human decision, TASK-219 QA finding 1; Software Architect role): migration
  0012 added to the scope (indexes on `attachment.clinical_entry_id` and `consent_grant(doctor_id, active)`),
  with upgrade/downgrade, `EXPLAIN`, negative-control and drift tests; `ask first` for existing databases;
  depends on TASK-219; size S → M; TS-018 ids corrected (TC-018.6 is taken); links to PRB-021, ADD-016,
  SOUP-009 and TASK-219 added. Stays `draft` (not started).
- 1.2 (2026-11-14) — Implemented (Software Developer): `GroupRepository.groups_for_account` (one join query, order
  unspecified as before), `groups_of` uses it; models and migration `0012_remaining_lookup_indexes`; tests
  `tests/groups/test_groups_of.py` (characterisation written and green on the old code first; query-count test
  failed there with `{1: 3, 10: 12, 100: 102}`) and `tests/db/test_migration_0012_indexes.py` (0012 applied only to
  throwaway testcontainers databases). `test_membership.py::test_groups_of_returns_groups_for_all_memberships`
  stubs `groups_for_account` instead of `get` per membership. TS-005 1.2 (TC-005.4) and TS-018 1.3 (TC-018.7,
  TC-018.8), both `in_review` with the approval removed. ADD-016 not edited (TASK-225). `in_review`.
- 1.3 (2026-11-14) — QA review round 1: CHANGES REQUESTED (1 HIGH: the module-gating path has no query-count test; 1 MEDIUM: PRB-024 not updated, premise wrong; 2 LOW). `in_review → draft`.
- 1.4 (2026-11-14) — round 2 (Software Developer): finding 1 `test_module_gate_query_count_constant` added (constant at 1, 10, 100; fails with `{1: 4, 10: 13, 100: 103}` when an N+1 is planted in `ModuleAccessGuard`, guard restored); finding 2 PRB-024 1.1 (latent, Investigation, Resolution; status left `open`); finding 3 stub test asserts the call and `[g1, g2]`; finding 4 TC-018.8 note; finding 5 PRB-082 refs. TS-005 and TS-018 list the module-gating case. `in_review`.
- 1.5 (2026-11-14) — QA review round 2: APPROVED (2 LOW carried: `/me/modules` case mirrors the router; TS round-2 edits without a version bump). Checkboxes ticked; `in_review → approved`.
