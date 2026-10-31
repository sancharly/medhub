---
id: "PRB-027"
type: problem-report
title: "Identity services compare roles directly instead of asking the authorization service"
status: open
version: "1.1"
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

Planned in CR-004: TASK-188 (identity and lifecycle services), TASK-189 (routers, plus a static
check that no access decision compares `user_type` outside `backend/app/authz/`). ADR-0006 is
the governing decision; no new ADR. Not yet fixed.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Simplicity / hygiene.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
