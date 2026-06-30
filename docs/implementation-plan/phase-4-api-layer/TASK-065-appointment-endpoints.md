# TASK-065 — Appointment endpoints

- **Phase:** 4 — API layer
- **Software item / unit:** SI-API / U-API-Routers, U-API-DTO
- **Implements:** SR-010 (create with doctor+patient+datetime, validation); SR-011 (visibility
  scoped to participants + admin); SR-035 (PENDING on create, patient notification, patient-only
  confirm/decline, state machine) — and the SR-036 grant linkage as a side effect
- **Depends on:** TASK-047 (AppointmentService.create), TASK-048 (state machine), TASK-049
  (consent link), TASK-051 (visibility / list_for) — must be merged first
- **Branch:** `feature/appointment-endpoints`
- **Status:** Completed

## Objective

Expose the SI-APPT HTTP surface: create an appointment (`POST /appointments`) which starts PENDING
and notifies the patient; list appointments scoped to the caller (`GET /appointments`); and the
**patient-only** confirm/decline transitions (`POST /appointments/{id}/confirm`,
`POST /appointments/{id}/decline`) which create / revoke the appointment-scoped consent grant
(SR-036). Routers delegate to `AppointmentService`; visibility and the patient-only rule are
authorized server-side. Traces to SR-010, SR-011, SR-035.

## Interfaces to honor

HTTP contract (verbatim from [api-design.md](../../specifications/api-design.md)):

| Method & path                     | Purpose                                               | Key reqs             |
|-----------------------------------|-------------------------------------------------------|----------------------|
| `POST /appointments`              | create (doctor, patient, datetime) → PENDING + notify | SR-010, SR-035.1/2   |
| `GET /appointments`               | list, scoped to caller (own/admin)                    | SR-011               |
| `POST /appointments/{id}/confirm` | patient only → CONFIRMED + grant consent              | SR-035.5/9, SR-036.1 |
| `POST /appointments/{id}/decline` | patient only → DECLINED + revoke that grant           | SR-035.6/7, SR-036.4 |

Consumes ([12-interfaces.md](../../design/12-interfaces.md) §12.1) **verbatim**:

```python
AppointmentService.create(self, actor: Account, doctor_id: UUID, patient_id: UUID,
                          scheduled_at: datetime) -> Appointment        # TASK-047
AppointmentService.confirm(self, id: UUID, patient: Account) -> Appointment   # TASK-048 (+TASK-049 grant)
AppointmentService.decline(self, id: UUID, patient: Account) -> Appointment   # TASK-048 (+TASK-049 revoke)
AppointmentService.list_for(self, actor: Account) -> list[Appointment]        # TASK-051
```

All endpoints declare the `require(action, resource_loader)` guard (TASK-025). `GET /appointments`
visibility: associated doctor, associated patient, and administrative personnel only (SR-011).
Confirm/decline are **patient-only** on the associated patient (SR-035.9); the consent grant
create/revoke is a server-side side effect of these transitions (SR-036.1/4), not a client action.

Must **not**: let the client set the initial state — creation always yields PENDING (SR-035.1);
allow a doctor or admin to confirm/decline on the patient's behalf (SR-035.9); require or expose
clinical data during creation (admin creates without clinical access, SR-010.4/SR-009); re-implement
the state machine or the grant linkage (those are TASK-048/049).

## Implementation detail

- Files to create:
  - `backend/app/api/routers/appointments.py` — `APIRouter(prefix="/appointments")` with the four
    endpoints; mounted under `/api/v1`.
  - `backend/app/api/schemas/appointment.py` — Pydantic v2 DTOs (camelCase):
    - `AppointmentCreateRequest { doctorId: UUID, patientId: UUID, scheduledAt: datetime }`
    - `AppointmentResponse { id, doctorId, patientId, scheduledAt, state }`
      (`state` ∈ `PENDING | CONFIRMED | DECLINED`)
    - `AppointmentListResponse { items: list[AppointmentResponse], nextCursor: str | None }`
      (paginated, access-scoped per api-design.md)
- `POST /appointments` (authorized creator — admin personnel or an involved participant, CSRF-checked):
  authorize `appointment:create`; `AppointmentService.create(actor, doctorId, patientId, scheduledAt)`
  validates that the references exist and are of the correct type and that `scheduledAt` is present
  (SR-010.1/2, server-side authoritative). The new appointment is **PENDING** (SR-035.1) and the
  patient notification (in-app + email) is enqueued as a side effect (SR-035.2/3, via TASK-050).
  201 `AppointmentResponse`. Audit `APPOINTMENT_CREATE` (SR-023).
- `GET /appointments` (authorized): authorize `appointment:list`; `AppointmentService.list_for(actor)`
  returns only appointments the caller may see — the associated doctor/patient or admin personnel
  (SR-011.1/2/3); unrelated users see none of others' appointments (SR-011.4). Each row carries the
  current confirmation state (SR-035.4/8). Paginated.
- `POST /appointments/{id}/confirm` (patient only, CSRF-checked): authorize `appointment:confirm` —
  caller must be the associated patient (SR-035.9); `confirm` transitions PENDING → CONFIRMED
  (SR-035.5) and creates the `APPOINTMENT:{id}` consent grant for the doctor (SR-036.1, via TASK-049).
  200 `AppointmentResponse`. Audit `APPOINTMENT_CONFIRM` with patient/doctor/appointment id (SR-035.10,
  SR-036.6).
- `POST /appointments/{id}/decline` (patient only, CSRF-checked): authorize `appointment:decline` —
  caller must be the associated patient (SR-035.9); `decline` transitions to DECLINED from PENDING or
  CONFIRMED (SR-035.6/7) and revokes **only** this appointment's grant (SR-036.4); the doctor's
  effective access is the union of any remaining grants (SR-036.4 Case B). 200. Audit
  `APPOINTMENT_DECLINE` (SR-035.10, SR-036.6).
- Edge cases: a non-participant calling `GET` simply does not see the appointment (404 on a direct
  `{id}` fetch / absent from the list); confirm/decline by a non-patient → 403; an invalid transition
  (e.g. confirm a DECLINED appointment) is rejected by the state machine → 409.
- Error cases (RFC 7807, base `https://medhub.example/errors/`): missing `doctorId`/`patientId`/
  `scheduledAt`, or references of the wrong type → `400 /errors/validation-error` (SR-010.2);
  unauthorized creator, or non-patient confirm/decline → `403 /errors/forbidden` (SR-035.9);
  appointment not visible/absent → `404 /errors/not-found`; invalid state transition → `409
  /errors/conflict`.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/api/test_appointments_router.py`):
  - admin creates with valid doctor/patient/datetime → 201, state PENDING, patient notification
    enqueued, no clinical-data read (SR-010.1/3/4, SR-035.1/2).
  - missing any of doctor/patient/datetime, or a wrong-type reference → 400 (SR-010.2).
  - `GET /appointments` returns only the caller's own (doctor/patient) or, for admin, all; an
    unrelated user sees none (SR-011.1/2/3/4).
  - patient confirms a PENDING appointment → 200 CONFIRMED and the appointment-scoped grant is
    created for the doctor (SR-035.5, SR-036.1).
  - patient declines a CONFIRMED appointment → 200 DECLINED and only that grant is revoked; a
    pre-existing manual grant survives (SR-035.7, SR-036.4 Case B).
  - doctor or admin attempting confirm/decline → 403 (SR-035.9).
  - confirming a DECLINED appointment → 409 (invalid transition).
  - confirm/decline audited with patient/doctor/appointment id (SR-035.10, SR-036.6).
  - state-changing endpoints reject a missing CSRF token → 403 (SR-031.3).
- Integration (`backend/tests/api/test_appointment_integration.py`): create → patient confirm →
  doctor can read clinical data → patient decline → doctor read denied (when no other grant),
  end-to-end through the test client (SR-036).

## Acceptance criteria

- [x] An authorized user creates an appointment with doctor, patient, datetime; missing/wrong-type → 400 (SR-010.1/2).
- [x] A created appointment is PENDING, persisted, retrievable, and the patient is notified (SR-035.1/2/3, SR-010.3).
- [x] Admin personnel create appointments without clinical-data access (SR-010.4).
- [x] `GET /appointments` is scoped to the associated doctor/patient and admin; unrelated users cannot see it (SR-011).
- [x] Only the associated patient can confirm/decline; doctors/admins cannot (SR-035.9).
- [x] Confirm → CONFIRMED + creates the appointment grant; decline → DECLINED + revokes only that grant (SR-035.5/6/7, SR-036.1/4).
- [x] Confirm/decline audited; state-changing requests are CSRF-protected (SR-035.10, SR-031.3). (TASK-069a)

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit + integration tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (four endpoints + DTOs)
- [x] Audit events emitted for security-relevant actions (create/confirm/decline — SR-023)
- [x] Traceability matrix row updated (SR-010, SR-011, SR-035 → TASK-065 → tests)
- [x] Security review N/A (authz/appointment services consumed, not implemented here)

## Audit verdict (2026-06-29)

- **Verdict:** FAIL (CSRF enforcement missing — resolved by TASK-069a)
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-069a completed. All AC/DoD items now satisfied.

## QA sign-off

- **Date:** 2026-06-30
- **Reviewer:** QA Engineer agent (phase-4 audit remediation)
- **Evidence:** CSRF gap closed by TASK-069a; OpenAPI regenerated in TASK-068a; 484 tests pass (ruff + mypy clean).
