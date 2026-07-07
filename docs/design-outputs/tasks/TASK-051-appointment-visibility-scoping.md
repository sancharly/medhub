---
id: "TASK-051"
type: task
title: "Appointment visibility scoping"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-011"
    relation: implements
  - target: "SR-035"
    relation: implements
  - target: "TASK-047"
    relation: relates_to
  - target: "TASK-027"
    relation: relates_to
tags: ["audit-verified", "phase:3-domain-services"]
---

- **Phase:** 3 — Domain services
- **Software item / unit:** SI-AUTHZ / U-AUTHZ-ApptVisibility
- **Implements:** SR-011 (AC-1 doctor sees own, AC-2 patient sees own, AC-3 admin sees for scheduling, AC-4 unrelated cannot see); SR-035 AC-8 (participants see confirmation state)
- **Depends on:** TASK-047 (appointment create / model), TASK-027 (API deps / authz guard) — must be merged first
- **Branch:** `feature/appointment-visibility`
- **Status:** Completed (audit-verified 2026-06-29)

## Objective

Scope appointment listing and retrieval to the caller: the associated doctor and patient see their appointments, administrative personnel see appointments for scheduling, and unrelated users see none. The doctor and admin can see the current confirmation state (SR-035 AC-8) but the scoping never exposes clinical data. Traces to SR-011 and SR-035 AC-8.

## Interfaces to honor

Implements the list/visibility part of `AppointmentService` from [12-interfaces.md](../../design/12-interfaces.md) §12.1 **verbatim**, applying the SI-AUTHZ visibility rule:

```python
class AppointmentService:
    def list_for(self, actor: Account) -> list[Appointment]: ...   # scoped to caller (SR-011)
    def get(self, actor: Account, appointment_id: UUID) -> Appointment: ...   # visibility-checked
```

- Visibility is decided by `AuthorizationService` (this unit, `U-AUTHZ-ApptVisibility`), not re-implemented inline in SI-APPT (§12.3 rule 1). The rule: `actor` is the appointment's doctor, the appointment's patient, or an administrative-personnel/sysadmin account → visible; otherwise not (deny-by-default, SR-005, SR-011 AC-4).
- The list query is **scoped at the repository level** (filtered by `actor`) — it must not fetch all appointments then filter in Python, both for correctness and SR-026 performance.
- Confirmation `state` is part of the appointment projection visible to doctor/patient/admin (SR-035 AC-8); no clinical fields are present on the appointment DTO at all (SR-010 AC-4 boundary).

## Implementation detail

- Files to create / modify:
  - `backend/app/authz/appointment_visibility.py` — `can_view_appointment(actor, appointment) -> bool` and the list-scoping predicate consumed by the repository query builder.
  - `backend/app/db/repositories/appointment_repository.py` — `list_for_actor(actor)`: for doctor → `doctor_id == actor.id`; for patient → `patient_id == actor.id`; for admin/sysadmin → all (or org-scoped) (parameterized; uses the `doctor_id`/`patient_id` indexes from TASK-047).
  - `backend/app/appointments/service.py` — `list_for`, `get` delegating visibility to the authz unit.
- Endpoint (SI-API): `GET /appointments` scoped to caller ([api-design.md](../../specifications/api-design.md)); collection is access-scoped and paginated (api-design conventions).
- Audit: appointment listing is not in SR-023's enumerated security-relevant set (no clinical-data access); do not over-audit. A denied `get` of a specific appointment by an unrelated user is a denied-access event — audit minimally per the central authz convention.
- Error cases (RFC 7807): unrelated user `get` → `404 /errors/not-found` (resource not visible to caller — avoids leaking existence/care-relationship, SR-011 AC-4) rather than 403; unauthenticated → `401 /errors/unauthenticated`.
- Edge cases: an admin sees appointments to schedule but the appointment DTO carries no clinical fields (SR-010 AC-4). A doctor sees only appointments where they are the named doctor — not all of a patient's appointments. A patient sees only their own. `404` (not `403`) is used for non-visible specific appointments so existence is not disclosed (SR-011 AC-4 privacy rationale — care relationships not leaked).

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/authz/test_appointment_visibility.py`):
  - associated doctor → appointment visible / in `list_for` (SR-011 AC-1).
  - associated patient → visible / in `list_for` (SR-011 AC-2).
  - administrative personnel → appointment visible for scheduling (SR-011 AC-3).
  - sysadmin → visible (admin role).
  - unrelated doctor (not the named doctor) → not in `list_for`; `get` → `404` (SR-011 AC-4).
  - unrelated patient → not visible; `get` → `404` (SR-011 AC-4).
  - `list_for` is repository-scoped (assert the query filters by actor, not post-filtered) (SR-011, SR-026).
  - visible projection includes confirmation `state` (SR-035 AC-8) and **no** clinical fields (SR-010 AC-4).
- Integration (`backend/tests/api/test_appointment_visibility_api.py`): three accounts create/own different appointments; `GET /appointments` returns only the caller's scoped set; unrelated `GET /appointments/{id}` → `problem+json` 404.

## Acceptance criteria

- [x] The associated doctor can view the appointment (SR-011 AC-1).
- [x] The associated patient can view the appointment (SR-011 AC-2).
- [x] Administrative personnel can view appointments for scheduling (SR-011 AC-3).
- [x] An unrelated, non-admin user cannot view the appointment; `GET /appointments` excludes it and `GET /appointments/{id}` returns 404 (SR-011 AC-4).
- [x] Doctor/patient/admin see the confirmation state; no clinical data is exposed on appointment DTOs (SR-035 AC-8, SR-010 AC-4).
- [x] List scoping is enforced in the repository query (not post-filtered) (SR-026).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit + integration tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (list endpoint, scoped/paginated)
- [x] Audit events emitted for security-relevant actions (denied specific-appointment access)
- [x] Traceability matrix row updated (SR-011, SR-035 AC-8 → TASK-051 → tests)
- [x] Security review completed (authorization/visibility code — SR-031.6)

## Audit verdict (2026-06-29)

- **Verdict:** PASS
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- Acceptance criteria verified met; boxes checked.
