# TASK-047 — Appointment create

- **Phase:** 3 — Domain services
- **Software item / unit:** SI-APPT / U-APPT-Crud
- **Implements:** SR-010 (AC-1 create with doctor+patient+datetime, AC-2 reject missing, AC-3 persisted/retrievable, AC-4 admin without clinical data)
- **Depends on:** TASK-027 (API deps / authz guard, current-user DI) — must be merged first
- **Branch:** `feature/appointment-create`
- **Status:** Completed (audit-verified 2026-06-29)

## Objective

Let an authorized user (administrative personnel, or the involved doctor/patient per visibility) create an appointment that links exactly one doctor and one patient at a given date/time, validating that both references exist and the datetime is present. A new appointment starts in **PENDING** (the state machine and the patient-only confirm/decline are TASK-048; consent linkage is TASK-049; notification is TASK-050). Administrative personnel can create appointments without touching clinical data. Traces to SR-010.

## Interfaces to honor

Implements the create part of `AppointmentService` from [12-interfaces.md](../../design/12-interfaces.md) §12.1 (provider SI-APPT; consumer SI-API) **verbatim**:

```python
class AppointmentService:
    def create(self, actor: Account, doctor_id: UUID, patient_id: UUID,
               scheduled_at: datetime) -> Appointment: ...
    # confirm/decline → TASK-048; list_for → TASK-051
```

- Authorizes via `AuthorizationService.authorize(actor, "appointment:create", ...)` (SR-005). Creation requires **no clinical-data access** — administrative personnel create appointments without any clinical read (SR-010 AC-4, SR-009).
- Validation is server-side authoritative (SR-031.5): referenced doctor must be an account of type doctor; patient of type patient; `scheduled_at` required.
- This unit sets the initial state to `PENDING` but does not implement transitions (that is TASK-048).

## Implementation detail

- Files to create:
  - `backend/app/appointments/service.py` — `AppointmentService.create`.
  - `backend/app/db/models/appointment.py` — `Appointment`: `id`, `doctor_id` (FK account), `patient_id` (FK account), `scheduled_at` (datetime), `state` (enum `PENDING|CONFIRMED|DECLINED`, default `PENDING`), `created_at`, `created_by` (FK account). FHIR-aligned (FHIR `Appointment`) per [fhir-mapping.md](../../specifications/fhir-mapping.md) (SR-021).
  - `backend/app/db/repositories/appointment_repository.py` — `add(appointment)`, `get(id)` (parameterized).
  - `backend/app/api/schemas/appointment.py` — Pydantic v2 DTO: request `{ doctorId, patientId, scheduledAt }`; response includes `id, doctorId, patientId, scheduledAt, state`.
  - `backend/app/db/alembic/versions/<rev>_appointment.py` — migration (state enum, indexes on `doctor_id`, `patient_id` for SR-011 scoping/SR-026).
- Endpoint (SI-API): `POST /appointments` → 201 PENDING ([api-design.md](../../specifications/api-design.md)). (Notification enqueue, TASK-050, hangs off this create.)
- Audit: record `appointment.create` (administrative action, SR-023 AC-4) with actor, doctor, patient.
- Error cases (RFC 7807): missing `doctorId`/`patientId`/`scheduledAt` → `400 /errors/validation-error` with `errors[]` (SR-010 AC-2); `doctorId` not a doctor or `patientId` not a patient, or either absent → `400 /errors/validation-error` (reference validation, SR-010 AC-1/AC-2); unauthorized creator → `403 /errors/forbidden`.
- Edge cases: doctor and patient must be distinct, existing, active accounts of the correct type. A past `scheduled_at` is accepted by this unit (no business rule forbids it in the SR); only presence is required (SR-010 AC-2). Initial state is always `PENDING` regardless of any client-sent state field.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/appointments/test_appointment_create.py`):
  - admin creates with valid doctor, patient, datetime → persisted, `state == PENDING`, retrievable (SR-010 AC-1/AC-3).
  - missing doctor / patient / datetime → `400 validation-error`, nothing persisted (SR-010 AC-2).
  - `doctorId` referencing a non-doctor (or patient referencing a non-patient) → `400` (SR-010 AC-1/AC-2).
  - non-existent doctor/patient id → `400`/`404` per reference rule, nothing persisted (SR-010 AC-2).
  - admin creates without any clinical-data read occurring (SR-010 AC-4) — assert no `ClinicalDataService` call.
  - unauthorized creator → `403`, denied access audited (SR-005, SR-023).
  - create audited (SR-023 AC-4).
- Integration (`backend/tests/api/test_appointment_create_api.py`): `POST /appointments` returns 201 PENDING and the row is retrievable; invalid payloads return `problem+json`.

## Acceptance criteria

- [x] An authorized user can create an appointment with a doctor, a patient, and a date/time (SR-010 AC-1).
- [x] Missing doctor, patient, or datetime is rejected (SR-010 AC-2).
- [x] Doctor/patient references are validated to exist and be of the correct type (SR-010 AC-1).
- [x] A created appointment is persisted, starts PENDING, and is retrievable (SR-010 AC-3).
- [x] Administrative personnel create appointments without accessing clinical data (SR-010 AC-4).
- [x] Creation is authorized and audited (SR-005, SR-023).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit + integration tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (create endpoint)
- [x] Audit events emitted for security-relevant actions (SR-023)
- [x] Traceability matrix row updated (SR-010 → TASK-047 → tests)
- [x] Security review N/A (authz consumed, not implemented here)

## Audit verdict (2026-06-29)

- **Verdict:** PASS
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- Acceptance criteria verified met; boxes checked.
