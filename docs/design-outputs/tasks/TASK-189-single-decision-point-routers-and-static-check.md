---
id: "TASK-189"
type: task
title: "Route router-level role checks through AuthorizationService and forbid new ones"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
links:
  - target: "SR-005"
    relation: implements
  - target: "SR-009"
    relation: implements
  - target: "SR-023"
    relation: implements
  - target: "SR-008"
    relation: implements
  - target: "RISK-001"
    relation: mitigates
  - target: "RISK-004"
    relation: mitigates
  - target: "RISK-006"
    relation: mitigates
  - target: "PRB-027"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "TASK-188"
    relation: relates_to
  - target: "ADD-007"
    relation: relates_to
  - target: "ADD-005"
    relation: relates_to
tags: ["security", "authz", "cr:CR-004", "control:design"]
---

# TASK-189 — Route router-level role checks through AuthorizationService and forbid new ones

- **Software item / unit:** SI-API `U-API-Routers` (ADD-005); SI-AUTHZ `U-AUTHZ-Policy`,
  `U-AUTHZ-AdminProjection` (ADD-007).
- **PRB:** PRB-027 (router part; found by the PRB-027 Investigation). **CR:** CR-004. **Design:** ADR-0006.
- **Depends on:** TASK-188.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (`api/routers/accounts.py`, `modules.py`, `consents.py`, `clinical.py`,
  `authz/service.py`; 2 test files; TS-002, TS-009)
- **Needs:** a Docker daemon for the real-database audit test.

## Objective

Close SR-023 AC 7 and SR-005 AC 1 for the routers: `accounts.py:134` (unlock),
`modules.py:38` (module list), `consents.py:45,67,82` (consent grant, revoke, list),
`clinical.py:114` (patient roster). Make the rule permanent with a static check.

## Implementation detail

1. Extend `backend/tests/authz/test_decision_table.py` with the current router behaviour; green
   before the move.
2. `AuthorizationService` rules: `account:unlock` (already in `lifecycle_actions`),
   `module:list` (SYSADMIN), `consent:grant`, `consent:revoke`, `consent:list` (PATIENT, own),
   `patient_roster:list` (DOCTOR). Routers call `authorize(...)`.
3. The admin projection choice (`accounts.py:83,107`) moves behind one authz-package function
   (`requires_admin_projection(actor)`, `U-AUTHZ-AdminProjection`); routers stop comparing roles.
4. `backend/tests/authz/test_no_role_decisions_outside_authz.py`: an AST scan of `backend/app` and
   `backend/modules` that fails on a comparison involving `.user_type` or `UserType.<member>`
   outside `backend/app/authz/`, except an explicit allow-list with a reason per entry (the
   non-decision comparisons in the PRB-027 Investigation: `appointments/service.py:51,55`,
   `auth/session.py:23-24`, `api/routers/lifecycle.py:85`, `identity/account_service.py:113`).

## Tests (write first)

- `backend/tests/authz/test_decision_table.py` (extended; unchanged results).
- `backend/tests/authz/test_no_role_decisions_outside_authz.py` (static; negative control: add
  `if actor.user_type == UserType.ADMIN:` to a router and see it fail).
- `backend/tests/api/test_accounts_router.py`, `test_consents_router.py`, `test_clinical_router.py`,
  `test_admin_projection_integration.py`: status codes and projections unchanged.
- `backend/tests/audit/test_authz_decision_audit.py` (extend, real database): denied unlock,
  denied module list, denied consent grant by a DOCTOR, denied roster by a PATIENT → one
  `AUTHZ_DENIED` row each.

## Acceptance criteria

- [ ] SR-005 AC 1, AC 3: no role comparison decides access outside `backend/app/authz/`
      (`backend/tests/authz/test_no_role_decisions_outside_authz.py`).
- [ ] SR-023 AC 7: the router decisions are audited (`backend/tests/audit/test_authz_decision_audit.py`).
- [ ] SR-009: the admin projection is unchanged (`backend/tests/api/test_admin_projection_integration.py`).

## Verification

```sh
cd backend && uv run pytest tests/authz tests/api tests/audit -v
cd backend && uv run pytest modules/dicom_viewer/tests -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
```

## Records

- **TS-002**: TC-002.8 (static check; router decisions in the table), `verifies` SR-005, SR-008, SR-009.
- **TS-009**: TC-009.10 extended (router decisions audited).
- **PRB-027**: `## Resolution` (TASK-188 and this task), `resolved`.

## Definition of Done

- [ ] Backend suite and DICOM module tests pass; coverage ≥ 85 %.
- [ ] TS-002, TS-009 `in_review`; PRB-027 `resolved`.
- [ ] `traceability-check` shows no error for TASK-189, TS-002, TS-009, SR-005, SR-023, PRB-027.
