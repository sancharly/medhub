---
id: "TASK-187"
type: task
title: "Decide and audit appointment scoping, appointment visibility and module access in AuthorizationService"
status: draft
version: "1.0"
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

- [ ] SR-005 AC 1, AC 3: appointment scoping, visibility and module access are decided by
      `AuthorizationService` only; the decision table is unchanged (`backend/tests/authz/test_decision_table.py`).
- [ ] SR-023 AC 7: each of those decisions, allowed or denied, writes an audit row with the full
      fields (`backend/tests/audit/test_authz_decision_audit.py`).
- [ ] SR-011 AC 4: a not-visible appointment is still answered 404
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

- [ ] Backend suite and DICOM module tests pass; coverage ≥ 85 %.
- [ ] TS-002 1.2, TS-009 updated, `in_review`; PRB-026 `resolved`.
- [ ] `traceability-check` shows no error for TASK-187, TS-002, TS-009, SR-005, SR-023, PRB-026.
