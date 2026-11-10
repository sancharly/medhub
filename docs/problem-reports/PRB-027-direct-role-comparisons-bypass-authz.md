---
id: "PRB-027"
type: problem-report
title: "Identity services compare roles directly instead of asking the authorization service"
status: resolved
version: "1.4"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-31"
criticality: major
links: []
tags: ["correctness", "hazard:privacy"]
---

# PRB-027 — Identity services compare roles directly instead of asking the authorization service

## Observed

`app/identity/account_service.py` and `app/identity/lifecycle.py` compare `user_type` directly rather than calling `AuthorizationService`, bypassing the single decision point required by ADR-0006.

## Impact

Same divergence and audit gap as PRB-026, on the account lifecycle paths (SR-032, SR-034).

## Investigation

Read on 2026-10-31 (CR-004 Plan stage, Software Architect role). **Present, and wider than
reported.** Direct `user_type` comparisons that decide access, outside `backend/app/authz/`:

| Location | Decision | Audited? |
|---|---|---|
| `backend/app/identity/account_service.py:119-126` (`_check_create_permission`) | who may create which account type (SR-032 AC 1, AC 4, AC 5) | no |
| `backend/app/identity/lifecycle.py:32,71` | SYSADMIN-only deactivate / reactivate (SR-034 AC 1) | no |
| `backend/app/identity/activation.py:118` | ADMIN or SYSADMIN may resend activation | no |
| `backend/app/identity/erasure.py:62` | SYSADMIN or the account itself may delete | no |
| `backend/app/api/routers/accounts.py:134` | SYSADMIN-only unlock | no |
| `backend/app/auth/lockout.py:102` (`admin_unlock`, `actor_role != "SYSADMIN"`) | a second copy of the unlock rule, found by QA in TASK-189 round 1 | no |
| `backend/app/api/routers/modules.py:38` | SYSADMIN-only module list | no |
| `backend/app/api/routers/consents.py:45,67,82` | PATIENT-only consent grant, revoke, list | no |
| `backend/app/api/routers/clinical.py:114` | DOCTOR-only patient roster | no |
| `backend/app/api/routers/accounts.py:83,107` | ADMIN gets the admin projection (SR-009) | n/a (projection, not a refusal) |

Each refusal raises `AuthorizationError` (403) without an `AUTHZ_DENIED` row, and each
permission is a second copy of a rule `AuthorizationService` also states
(`backend/app/authz/service.py:145-169` lists `account:create`, `account:deactivate`, …). The two
copies can diverge (ADR-0006).

Comparisons that are **not** access decisions and stay: `backend/app/appointments/service.py:51,55`
(the referenced doctor and patient must have those roles, a data rule of SR-010),
`backend/app/auth/session.py:23-24` (inactivity timeout by role, SR-030),
`backend/app/api/routers/lifecycle.py:85` (confirmation of the typed account type, SR-034) and
`backend/app/identity/account_service.py:113` (building the resource descriptor).

## Safety evaluation

Contributes to RISK-001 and RISK-006.

## Resolution

Fixed by TASK-188 (identity services) and TASK-189 (routers, lockout, static check) under CR-004.
ADR-0006 is the governing decision; no new ADR. Every row of the Investigation table is closed:

- `account_service.py` `_check_create_permission`, `lifecycle.py` deactivate and reactivate,
  `activation.py` resend, `erasure.py` delete (TASK-188): the services call
  `AuthorizationService.decide()` (`backend/app/authz/service.py`, `_eval_identity`) for
  `account:create`, `account:deactivate`, `account:reactivate`, `account:delete` and
  `activation:resend`; each writes one `AUTHZ_ALLOWED`/`AUTHZ_DENIED` row and keeps its refusal
  message. `account:create` denies every role unless a requested type is stated, and an ADMIN
  asking for SYSADMIN.
- `accounts.py` unlock, `modules.py` module list, `consents.py` grant/revoke/list, `clinical.py`
  roster (TASK-189): the routers call `decide()` with `account:unlock`, `module:list`,
  `consent:grant`, `consent:revoke`, `consent:list`, `patient_roster:list` (one role each, map
  `_ROLE_ONLY_ACTIONS`); status codes and messages unchanged.
- `lockout.py` (TASK-189 round 2): `LockoutService.admin_unlock` no longer takes `actor_role` or
  checks it; the unlock decision is the router's `account:unlock`, audited.
- The admin projection choice (`accounts.py`) is `requires_admin_projection(actor)` in
  `backend/app/authz/admin_projection.py`; the routers compare no role.
- The rule is permanent: `backend/tests/authz/test_no_role_decisions_outside_authz.py` (AST scan of
  `backend/app` and `backend/modules`) fails on a role use outside `backend/app/authz/`: a
  comparison, a `match` value, a subscript or `.get()` keyed on a role, or a method call on a role,
  where a role is `.user_type`/`.role`, `UserType.<member>`, a role-name string, or a parameter or
  local name derived from one. Six exact expressions are listed as non-decisions, each with its
  reason: the SR-010 data rule in `AppointmentService.create` (2), the SR-030 inactivity timeout in
  `SessionService._inactivity_ttl` (`auth/session.py`), the typed-type confirmation in
  `delete_account`, the resource descriptor in `AccountService.get_profile`, and the auto-group
  query filter in `GroupRepository.list_auto_groups_for_type`. A new use inside one of those
  functions is a different expression and fails. Not followed: a role returned from another
  function.

Evidence (TS-003 TC-003.6, TS-002 TC-002.7/TC-002.8, TS-009 TC-009.10): the decision tables in
`backend/tests/authz/test_decision_table.py` were written green against the old code and stay
green after the move; real-database audit rows in
`backend/tests/audit/test_authz_decision_audit.py`. Reproduce:

```sh
cd backend && uv run pytest tests/authz tests/identity tests/api tests/audit tests/auth -q
cd backend && uv run pytest tests/authz/test_no_role_decisions_outside_authz.py -q
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
```

Limit: as for PRB-026, an allowed decision's row is lost when the request then fails (PRB-060).

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Simplicity / hygiene.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
- 1.2 (2026-10-31) — TASK-188: interim Resolution note (service part done; TASK-189 resolves). Status and criticality unchanged.
- 1.3 (2026-10-31) — TASK-189: `## Resolution` written; status `resolved` (CR-004 carries the `resolves` link). Criticality unchanged.
- 1.4 (2026-10-31) — TASK-189 round 2: `lockout.py` added to the Investigation and Resolution (QA finding 1); the Resolution describes the strengthened static check and its six exceptions. Status stays `resolved`.
