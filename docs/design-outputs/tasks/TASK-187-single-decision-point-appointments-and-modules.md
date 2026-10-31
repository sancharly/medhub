---
id: "TASK-187"
type: task
title: "Decide and audit appointment scoping, appointment visibility and module access in AuthorizationService"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
links:
  - target: "SR-005"
    relation: implements
  - target: "SR-011"
    relation: implements
  - target: "SR-015"
    relation: implements
  - target: "SR-023"
    relation: implements
  - target: "RISK-001"
    relation: mitigates
  - target: "RISK-004"
    relation: mitigates
  - target: "RISK-006"
    relation: mitigates
  - target: "PRB-026"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "TASK-137"
    relation: relates_to
  - target: "ADD-007"
    relation: relates_to
tags: ["security", "authz", "cr:CR-004", "control:design"]
---

# TASK-187 — Decide and audit appointment scoping, appointment visibility and module access in AuthorizationService

- **Software item / unit:** SI-AUTHZ `U-AUTHZ-Policy`, `U-AUTHZ-ApptVisibility`,
  `U-AUTHZ-ModuleGuard` (ADD-007); SI-APPT `U-APPT-Crud`; SI-API `U-API-Deps`.
- **PRB:** PRB-026. **CR:** CR-004. **Design:** ADR-0006 (single decision point; no new ADR).
- **Depends on:** TASK-137 (decisions are audited with the address). First of three authorization
  tasks: TASK-188 and TASK-189 extend the decision table this task creates and edit
  `backend/app/authz/service.py` after it.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (`authz/service.py`, `authz/appointment_visibility.py`, `appointments/service.py`,
  `api/deps.py`; 3 test files; TS-002, TS-009)
- **Needs:** a Docker daemon for the real-database audit test.

## Objective

SR-005 AC 1, AC 3 (one deny-by-default mechanism), SR-023 AC 7 (every decision audited with
actor, action, target, outcome, time and address). The PRB-026 Investigation: the list scope is
decided in `AppointmentService.list_for` (`appointments/service.py:158-171`), single reads in
`can_view_appointment` (`authz/appointment_visibility.py:12-20`) with no audit, module access in
`require_module_enabled` (`api/deps.py:195-211`) with no audit, and an unused, session-leaking
factory (`api/deps.py:107-144`, `authz/service.py:179-193`).

## Implementation detail

1. **Characterisation first.** `backend/tests/authz/test_decision_table.py`: a table of
   (role, action, ownership/consent/membership, expected allow) for every decision this task
   moves, run against the **current** code and committed green before any move. It must stay
   green, unchanged, after the move (RISK-004 control).
2. `AuthorizationService` gains:
   - `appointment_scope(actor) -> AppointmentScope` (`ALL`, `AS_DOCTOR(id)`, `AS_PATIENT(id)`,
     `NONE`), audited as the `appointment:list` decision (allowed with the scope as basis, or
     denied);
   - `authorize(actor, "appointment:read", Resource(owner_id=patient, ...))` using the visibility
     rule, which moves into `_evaluate` (the module `appointment_visibility.py` becomes a private
     helper of the policy or is removed);
   - `authorize(actor, "module:access", Resource(resource_type="module", ...))` with the
     `ModuleAccessGuard` result as an input.
3. `AppointmentService.list_for` asks for the scope and calls the matching repository method; it
   compares no role. `AppointmentService.get` calls `authorize(... "appointment:read" ...)`; on
   denial the service converts the `AuthorizationError` to `NotFoundError` (SR-011 AC 4), and the
   `AUTHZ_DENIED` row is already written (independent transaction, ADR-0016).
4. `require_module_enabled` calls `authorize(..., "module:access", ...)`.
5. Remove `require()`, `_get_authz_service()` (`api/deps.py:107-144`) and
   `get_authorization_service()` (`authz/service.py:179-193`): unused, and the factory leaks a
   session.

## Tests (write first)

- `backend/tests/authz/test_decision_table.py` (above; unit, fakes).
- `backend/tests/authz/test_authorization_service.py`, `backend/tests/authz/test_appointment_visibility.py`,
  `backend/tests/appointments/test_appointment_create.py`, `backend/tests/modules/test_module_gating.py`:
  updated to the new calls; denials raise as before.
- `backend/tests/audit/test_authz_decision_audit.py` (real database, `create_app()`): an allowed
  and a denied appointment list, a denied single read (404 to the client, `AUTHZ_DENIED` row
  present with address), an allowed and a denied module access → one row each with actor,
  action, target, outcome, timestamp, address.

## Acceptance criteria

- [x] SR-005 AC 1, AC 3: appointment scoping, visibility and module access are decided by
      `AuthorizationService` only; the decision table is unchanged (`backend/tests/authz/test_decision_table.py`).
- [x] SR-023 AC 7: each of those decisions, allowed or denied, on a request that completes, writes an
      audit row with the full fields (`backend/tests/audit/test_authz_decision_audit.py`). An allowed
      row is lost when the request then fails: PRB-060 (accepted by the human, 2026-10-31).
- [x] SR-011 AC 4: a not-visible appointment is still answered 404
      (`backend/tests/api/test_appointments_router.py`).

## Verification

```sh
cd backend && uv run pytest tests/authz tests/appointments tests/modules tests/audit tests/api/test_appointments_router.py -v
cd backend && uv run pytest modules/dicom_viewer/tests -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
```

Negative control: make `list_for` branch on the role again with the scope ignored; the audit test
fails for the list. Record the result.

## Records

- **TS-002** → 1.2 (`in_review`): TC-002.7 (decision table of moved decisions; characterisation
  before and after), `verifies` SR-005, SR-011, SR-015.
- **TS-009**: TC-009.10 (every decision audited: appointments, modules), `verifies` SR-023.
- **ADD-007** 1.1: confirm the unit text.
- **PRB-026**: `## Resolution`, `resolved`.

## Definition of Done

- [x] Backend suite and DICOM module tests pass; coverage ≥ 85 %.
- [x] TS-002 1.2, TS-009 updated, `in_review`; PRB-026 `resolved`.
- [x] `traceability-check` shows no error for TASK-187, TS-002, TS-009, SR-005, SR-023, PRB-026.

## Implementation notes

Order followed (RISK-004 control): `backend/tests/authz/test_decision_table.py` (37 cases, 38 after round 2) was written and
run green against the unchanged code (37 passed), then the logic moved, then the same file (unchanged) was run again (37 passed).

- `app/authz/service.py`: `Resource` gains optional `doctor_id`, `resource_id`, `module_enabled`;
  `AppointmentScope`/`AppointmentScopeKind` (`ALL`, `AS_DOCTOR`, `AS_PATIENT`, `NONE`);
  `AuthorizationService.appointment_scope(actor)` (audited `appointment:list` decision, then the scope by role);
  `appointment:read` (the visibility rule, now in `_evaluate`) and `module:access` (allowed only when the
  guard result passed in `Resource.module_enabled` is true). `resource_id` is the audit target when set
  (appointment id, module key). `get_authorization_service()` removed.
- `app/authz/appointment_visibility.py` removed (no remaining caller).
- `app/appointments/service.py`: `list_for` asks for the scope and calls the matching repository method, no role
  comparison; `get` authorizes `appointment:read` and converts `AuthorizationError` to `NotFoundError`
  (the `AUTHZ_DENIED` row is already written on its own transaction, ADR-0016).
- `app/api/deps.py`: `require_module_enabled` computes the guard result and calls
  `authorize(..., "module:access", ...)`; the 403 keeps its message. `require()` and `_get_authz_service()` removed.
- Tests: `tests/authz/test_appointment_visibility.py` now goes through `authorize`; `tests/modules/test_module_gating.py`
  and `test_router_mount.py` override `get_db` and stub `AuditService.record` (the gate now audits);
  `tests/authz/test_authorization_service.py`, `tests/api/test_appointments_router.py::TestGetAppointment` and the real-database
  `tests/audit/test_authz_decision_audit.py` (6 tests) added.

Behaviour changes (intended, SR-023 AC 7): a refused single appointment read and a refused module access now write an
`AUTHZ_DENIED` row (they wrote none); an allowed appointment list, single read and module access now write an
`AUTHZ_ALLOWED` row. Responses, status codes and messages are unchanged. Every allowed module request now adds one
audit row (volume note for TASK-188/189 and ops).

## Verification results

- `uv run pytest tests/authz tests/appointments tests/modules tests/audit tests/api/test_appointments_router.py`: 179 passed.
- `uv run pytest modules/dicom_viewer/tests`: 21 passed.
- Full `uv run pytest --cov=app --cov-fail-under=85`: 690 passed, 4 skipped, 92.52 % coverage.
- `ruff check .`, `black --check .`, `mypy app`: clean.
- Negative controls: `list_for` branching on the role again (scope ignored) fails
  `test_allowed_appointment_list_writes_one_row` and `test_denied_appointment_list_writes_one_row`;
  the visibility rule weakened to always allow fails three `test_decision_table.py` cases
  (`test_read_visibility[PATIENT-unrelated-False]`, `[DOCTOR-unrelated-False]`,
  `test_doctor_with_active_consent_still_cannot_read_unrelated_appointment`).

## QA review (2026-10-31, round 1): CHANGES REQUESTED

The code move itself is correct: the decision table passes 37/37 against the **pre-change** code
(HEAD `ef1d6c0` in a detached worktree, `appointment_visibility.py` present) and 37/37 after; no
status code or message changed; the removed `require()`, `_get_authz_service()`,
`get_authorization_service()` and `can_view_appointment` have no remaining caller (backend,
`modules/dicom_viewer`, docs other than the historical TASK-051); exactly one row per decision on
the tested paths. Two findings block approval, both fixable without touching the move.

1. **[HIGH] An allowed module-access decision leaves no audit row when the module request then
   fails** — `backend/app/authz/service.py:84-92` (`AUTHZ_ALLOWED`, outcome SUCCESS, joins the request
   transaction per ADR-0016) with `backend/app/db/repositories/session.py:28-32` (`get_db` rolls back
   on any exception). QA probe (real PostgreSQL, `create_app()`, module route raising
   `ValidationProblem` behind an enabled gate): response 400, **zero** rows for the actor. Reachable
   in production through `modules/dicom_viewer/dicom_viewer/router.py:54-55` (frame out of range,
   wrong content type → 400) and the 502 checksum path: the attachment was read, the module and
   clinical decisions were both allowed, nothing is audited. SR-023 AC 7: "No allowed or denied
   access is decided without such an entry"; this task's AC 2 and TS-009 TC-009.10 ("every ...
   decision, allowed or denied, writes one row") claim it. The clinical `AUTHZ_ALLOWED` row has the
   same loss (pre-existing, not this task's).
   → Either (a) commit `AUTHZ_ALLOWED` independently too (add it to `_INDEPENDENT_ACTIONS` in
   `backend/app/audit/service.py:20`; an ADR-0016 amendment, a second pooled connection per allowed
   decision, so weigh PRB-058 first), plus a real-DB test "allowed module access, handler raises →
   one `AUTHZ_ALLOWED` row"; or (b) if the human accepts the rollback, open a PRB (SR-023 AC 7,
   RISK-006), record it under RISK-006 "Risks introduced by controls", and narrow this task's AC 2
   and TS-009 TC-009.10 to "on a request that completes", with the PRB cited. Option (b) is the
   smaller change and keeps the move out of the audit write path.
2. **[MEDIUM] PRB-026 left `open` contradicts the plan; its interim note names tasks that do not
   resolve it** — `docs/problem-reports/PRB-026-authz-logic-in-persistence-layer.md:59-62`. CR-004
   maps PRB-026 to TASK-187 only (`CR-004`:221); this task's Records and DoD say `## Resolution`,
   `resolved`; TASK-188 and TASK-189 implement PRB-027, not PRB-026, and link it nowhere. Every item
   of the PRB-026 Investigation (list scope, single reads, module gate, dead factory) is done here,
   so as written the PRB would stay open with no resolving task.
   → Write the `## Resolution` (what moved, TC-002.7/TC-009.10 evidence, commit) and set `resolved`
   (the CR-004 `resolves` link already exists). If PRB-026 is meant to stay open, change the plan
   (CR-004 table, TASK-188/189 links and DoD) instead; do not leave the two disagreeing.
3. **[LOW] "Messages unchanged" has no test** — `backend/tests/authz/test_decision_table.py:193`
   asserts only the status code; `backend/tests/api/test_appointments_router.py:107-122` only the 404.
   No test asserts the module 403 detail or that a missing and a not-visible appointment give the
   same body (SR-011 AC 4). Code inspection shows identical strings. → Assert `resp.json()["detail"]`
   in the module rows of the table and compare the missing/not-visible 404 bodies.
4. **[LOW] The decision table has no denied-list row** — the only `appointment:list` denial (actor
   with no known role) is covered in `test_authorization_service.py` and the real-DB test, not in
   the characterisation table. → Optional: add it to the table for TASK-188/189 to extend.

Observations (not findings):
- Audit volume: a DICOM study view now writes the module `AUTHZ_ALLOWED`, the clinical
  `AUTHZ_ALLOWED` and `DICOM_STUDY_READ` per frame request. Already in the CR-004 plan risks and
  RISK-006 (SR-026, timings in TASK-202); one in-transaction insert per request is far below the
  NFR-008/SR-026 3 s budget.
- Module-gating unit tests stub `AuditService.record` and override `get_db`; that hides nothing,
  because `test_authz_decision_audit.py::test_module_access_decision_writes_one_row[True/False]`
  runs the real gate against a real database.
- The TS-009 TC-009.9 correction (worker tests patch `record`, so they are not no-address evidence)
  is right.
- ADD-007 and `docs/design/05-building-blocks.md:56` still list `U-AUTHZ-ApptVisibility` as a unit;
  it is now `AuthorizationService._eval_appointment_read`. ADD-007:63-72 describes this adequately.

Verification run by QA:
- Pre-change characterisation: worktree of HEAD, `test_decision_table.py` copied in → 37 passed.
- Targeted suite: 179 passed. `modules/dicom_viewer/tests`: 21 passed. Full suite with coverage:
  690 passed, 4 skipped, 92.52 %. `ruff`, `black --check`, `mypy app`: clean. OpenAPI export identical
  to `backend/openapi/openapi.json`; generated files untouched.
- Negative controls (pytest plugin, no source edit): `module:access` always allowed → 16 failures
  (12 table rows, 3 gating/mount tests, the real-DB denied module test); `appointment_scope`
  returning `ALL` for a doctor → `test_list_scope_by_role[DOCTOR]` fails.
- Traceability (TASK-187, TS-002, TS-009, PRB-026, SR-005/011/015/023): 0 errors, 9 warnings, all
  pre-existing or cleared on approval (TP-001 → TS-002/TS-009 `in_review`).


## Round 2 (software developer, 2026-10-31)

1. Finding 1 (HIGH), option (b) chosen by the human: PRB-060 created (`open`, `minor`; not linked from
   CR-004, out of its scope; the fix waits for PRB-058). AC 2 here and TC-009.10 in TS-009 narrowed to "on a
   request that completes". The lost-row behaviour is pinned by
   `tests/audit/test_authz_decision_audit.py::test_allowed_row_is_lost_when_the_handler_then_fails_prb_060`.
   RISK-006 (human-approved, not edited) needs a PRB-060 note under "Risks introduced by controls".
2. Finding 2: PRB-026 `## Resolution` written, status `resolved`, version 1.3.
3. Finding 3: `test_decision_table.py` asserts the module 403 `detail`; `test_appointments_router.py`
   asserts a missing and a not-visible appointment return the identical 404 body.
4. Finding 4: denied-list row added to the decision table (`test_list_denied_for_actor_with_no_known_role`).

## QA review (2026-10-31, round 2): APPROVED

Round-1 findings, all closed:

1. Finding 1 (HIGH): closed by option (b), which the human chose. PRB-060 is `open` and `minor`. Its
   Investigation gives file:line references, its Safety evaluation explains why it is `minor`, and it
   says no notification is needed because there is no release. The narrowed wording ("on a request that completes",
   citing PRB-060) matches in AC 2 here, in TS-009 TC-009.10 and its data-flow line, and in the PRB.
   The pinning test is real. A QA plugin added `AUTHZ_ALLOWED` to `_INDEPENDENT_ACTIONS`, and only
   `test_allowed_row_is_lost_when_the_handler_then_fails_prb_060` failed.
2. Finding 2 (MEDIUM): closed. PRB-026 is `resolved` 1.3. The Resolution covers each Investigation
   item and gives `cd backend` commands that QA re-ran. The CR-004 `resolves` link exists.
3. Finding 3 (LOW): closed. The module 403 `detail` is asserted in the table. The identical 404 body
   test also passes on the pre-change code (HEAD `ef1d6c0`), so it describes the old behaviour.
4. Finding 4 (LOW): closed. The denied-list row is in the table, and TS-002 TC-002.7 now says 38 cases.

Remaining observations (LOW, not blocking):
- RISK-006 "Risks introduced by controls" does not yet mention PRB-060. The round-2 note leaves it to
  "a later task" but names none. Add it to TASK-202, which revises RISK-006.
- PRB-026 Resolution says "Full suite: 690 passed". With round 2 it is 693, and no build commit is
  named. Update the figures when the commit is made.
- TASK-187 has no `relates_to` link to PRB-060. Optional.

Verification run by QA (round 2):
- Pre-change characterisation: the new `test_decision_table.py` in a detached worktree of HEAD
  `ef1d6c0` gave 38 passed. In the same worktree, `TestGetAppointment` gave 1 pass (identical 404
  body) and 1 expected failure (the `AUTHZ_DENIED` row, a new behaviour).
- Targeted suite: 182 passed. `modules/dicom_viewer/tests`: 21 passed. Full suite: 693 passed, 4 skipped,
  92.52 %. `ruff`, `black --check` and `mypy app` are clean. The OpenAPI export is identical to the committed file.
- Negative controls: with `module:access` always allowed, 16 tests fail. With the doctor scope set to `ALL`,
  `test_list_scope_by_role[DOCTOR]` fails. With `AUTHZ_ALLOWED` made independent, the PRB-060 pin fails.
- Traceability (TASK-187, TS-002, TS-009, PRB-026, PRB-060): 0 errors. There were 2 warnings, both
  TP-001 → TS-002/TS-009 `in_review`, and they clear with this approval.

## Version history

- 1.1 (2026-10-31) — Implemented; handed to QA (`in_review`). Implementation notes and verification results added.
- 1.1 (2026-10-31) — QA review round 1: CHANGES REQUESTED (`in_review → draft`); findings 1–4 recorded.
- 1.2 (2026-10-31) — Round 2: QA findings 1–4 addressed; handed back to QA (`in_review`).
- 1.2 (2026-10-31) — QA review round 2: APPROVED (`in_review → approved`); TS-002 and TS-009 approved.
