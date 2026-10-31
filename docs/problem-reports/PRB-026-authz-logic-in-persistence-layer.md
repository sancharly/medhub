---
id: "PRB-026"
type: problem-report
title: "Role-based authorization is embedded in the persistence layer"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-31"
criticality: major
links: []
tags: ["correctness", "hazard:privacy"]
---

# PRB-026 — Role-based authorization is embedded in the persistence layer

## Observed

`app/db/repositories/appointment_repo.py:29` — `list_for_actor` branches on the actor's role inside the repository, so an authorization decision lives outside `AuthorizationService`, against ADR-0006's single decision point.

## Impact

SR-005 deny-by-default is evaluated in two places, so the two can diverge; the repository decision is not audited.

## Investigation

Read on 2026-10-31 (CR-004 Plan stage, Software Architect role). **The location in "Observed" is
stale; the defect moved one layer up and is still present.**

- `list_for_actor` no longer exists. Commit `eca0a68` ("Move role dispatch out of
  AppointmentRepository into AppointmentService") left the repository with plain
  `list_for_doctor`, `list_for_patient` and `list_all` (`backend/app/db/repositories/appointment_repo.py:16-30`).
- The role branch now sits in `AppointmentService.list_for` (`backend/app/appointments/service.py:158-171`):
  `AuthorizationService` is asked only whether the role may list at all (`appointment:list`,
  allowed for every role, `backend/app/authz/service.py:112-113,117-118,141,164-165`), and the
  service then decides **which** appointments by comparing `user_type` itself. That scoping
  decision is not audited.
- Single-appointment reads are decided by `can_view_appointment`
  (`backend/app/authz/appointment_visibility.py:12-20`, called at `service.py:175`), a second
  policy function outside `AuthorizationService.authorize`; a refusal raises `NotFoundError`
  (SR-011 AC 4) and writes no audit row.
- Also found: `require()` and `_get_authz_service()` (`backend/app/api/deps.py:107-144`) are
  unused, and the factory they call, `get_authorization_service()`
  (`backend/app/authz/service.py:179-193`), takes `next(get_db())` without ever closing the
  session, so an `AUTHZ_ALLOWED` row written through it would never be committed. Dead code
  today; it is removed rather than fixed.
- The module-access decision (`require_module_enabled`, `deps.py:195-211`, using
  `ModuleAccessGuard`) refuses with 403 and writes no audit row either (SR-023 AC 7 names
  modules).

Not recommended for rejection: the decision is still outside the single decision point.

## Safety evaluation

Contributes to RISK-001 (unauthorized disclosure) and RISK-006 (an unaudited decision).

## Resolution

Planned in CR-004: TASK-187 (appointment scoping, appointment visibility and module access
decided and audited by `AuthorizationService`; the dead factory removed). ADR-0006 is the
governing decision; no new ADR. Not yet fixed.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Simplicity / hygiene.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
