# TASK-048 — Appointment state machine (confirm / decline)

- **Phase:** 3 — Domain services
- **Software item / unit:** SI-APPT / U-APPT-State
- **Implements:** SR-035 (AC-5 confirm, AC-6 decline pending, AC-7 decline confirmed, AC-9 patient-only, AC-10 audited)
- **Depends on:** TASK-047 (appointment create) — must be merged first
- **Branch:** `feature/appointment-state`
- **Status:** Completed

## Objective

Implement the appointment confirmation state machine — PENDING → CONFIRMED, PENDING → DECLINED, CONFIRMED → DECLINED — and enforce that **only the patient** associated with the appointment may confirm or decline; the doctor and administrative personnel cannot act on the patient's behalf. Each confirm/decline is audited. The consent grant/revoke side effect is layered on top in TASK-049; this unit owns the transitions and the patient-only rule. Traces to SR-035 criteria 5–7, 9, 10.

## Interfaces to honor

Implements confirm/decline of `AppointmentService` from [12-interfaces.md](../../design/12-interfaces.md) §12.1 **verbatim**:

```python
class AppointmentService:
    def confirm(self, patient: Account, appointment_id: UUID) -> Appointment: ...
    def decline(self, patient: Account, appointment_id: UUID) -> Appointment: ...
```

- The acting party is the **patient**; the service authorizes that `patient.id == appointment.patient_id` via `AuthorizationService` (action `appointment:confirm` / `appointment:decline`). A doctor or admin calling these is denied (SR-035 AC-9). Deny-by-default (SR-005).
- This unit performs only the state transition and its audit; it **must not** itself create or revoke consent grants — TASK-049 wires the consent side effect by composing over confirm/decline (single source of truth for transitions).

## Implementation detail

- Files to create / modify:
  - `backend/app/appointments/service.py` — add `confirm`, `decline`, and a private `_transition(appointment, target_state)` enforcing the allowed edges.
  - `backend/app/appointments/state.py` — the transition table: allowed = {PENDING→CONFIRMED, PENDING→DECLINED, CONFIRMED→DECLINED}; disallowed (e.g. DECLINED→CONFIRMED, CONFIRMED→CONFIRMED, transition of an already-DECLINED) raise an invalid-state error. Keep it a pure, table-driven function for unit testing.
  - `backend/app/db/repositories/appointment_repository.py` — `update_state(id, state)` (parameterized).
- Endpoints (SI-API): `POST /appointments/{id}/confirm`, `POST /appointments/{id}/decline` ([api-design.md](../../specifications/api-design.md)).
- Audit (SR-035 AC-10): each confirm/decline records `appointment.confirm` / `appointment.decline` with **patient identity, doctor identity, appointment id, action, timestamp** (exact fields from SR-035 AC-10).
- Error cases (RFC 7807): non-patient (doctor/admin/other patient) caller → `403 /errors/forbidden` (SR-035 AC-9); appointment not found / not visible → `404 /errors/not-found`; disallowed transition (e.g. confirm an already-declined, or re-confirm) → `409 /errors/conflict` (invalid state transition); confirm of an already-CONFIRMED → `409` (idempotency choice documented; default reject).
- Edge cases: SR-035 AC-7 explicitly allows CONFIRMED → DECLINED (patient changes their mind), so that edge is valid; DECLINED is terminal for re-confirmation in MVP (no requirement to re-confirm a declined appointment — a disallowed edge returns 409). The patient-only rule (AC-9) is enforced server-side and cannot be delegated; an admin who can otherwise see the appointment (SR-011) still cannot confirm/decline.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/appointments/test_appointment_state.py`):
  - patient confirms a PENDING appointment → state CONFIRMED (SR-035 AC-5).
  - patient declines a PENDING appointment → state DECLINED (SR-035 AC-6).
  - patient declines a CONFIRMED appointment → state DECLINED (SR-035 AC-7).
  - doctor attempts confirm/decline → `403`, state unchanged (SR-035 AC-9).
  - administrative personnel attempts confirm/decline → `403`, state unchanged (SR-035 AC-9).
  - a different patient attempts confirm/decline → `403` (SR-035 AC-9).
  - disallowed edge (re-confirm a DECLINED; confirm an already-CONFIRMED) → `409`, state unchanged (state-machine integrity).
  - confirm and decline each emit an audit event with patient, doctor, appointment id, action, timestamp (SR-035 AC-10).
- `backend/tests/appointments/test_state_table.py`: pure transition-table test for every (from, to) pair.
- Integration (`backend/tests/api/test_appointment_state_api.py`): confirm/decline through routers; non-patient gets `problem+json` 403.

## Acceptance criteria

- [ ] A patient can confirm a PENDING appointment → CONFIRMED (SR-035 AC-5).
- [ ] A patient can decline a PENDING appointment → DECLINED (SR-035 AC-6).
- [ ] A patient can decline a previously CONFIRMED appointment → DECLINED (SR-035 AC-7).
- [ ] Only the associated patient may confirm/decline; doctor and admin are denied (SR-035 AC-9).
- [ ] Disallowed transitions are rejected with 409; state is never corrupted.
- [ ] Each confirm/decline is audited with patient, doctor, appointment id, action, timestamp (SR-035 AC-10).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit + integration tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (confirm/decline endpoints)
- [ ] Audit events emitted for security-relevant actions (SR-023, SR-035 AC-10)
- [ ] Traceability matrix row updated (SR-035 → TASK-048 → tests)
- [ ] Security review N/A (authz consumed; patient-only rule covered by tests)
