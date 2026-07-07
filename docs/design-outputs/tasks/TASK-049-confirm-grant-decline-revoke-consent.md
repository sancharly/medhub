---
id: "TASK-049"
type: task
title: "Confirm → grant / decline → revoke consent"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-036"
    relation: implements
  - target: "TASK-048"
    relation: relates_to
  - target: "TASK-028"
    relation: relates_to
tags: ["phase:3-domain-services"]
---

- **Phase:** 3 — Domain services
- **Software item / unit:** SI-APPT / U-APPT-ConsentLink
- **Implements:** SR-036 (AC-1 grant on confirm, AC-3 no grant while pending/declined, AC-4 Cases A/B/C scoped revoke, AC-5 grant persists, AC-6 audited, AC-7 unified view)
- **Depends on:** TASK-048 (appointment state machine), TASK-028 (`ConsentService` / `ConsentGrant` per-source model) — must be merged first
- **Branch:** `feature/appointment-consent-link`
- **Status:** Completed

## Objective

Tie clinical-data consent to the patient's appointment confirmation: confirming an appointment creates an `APPOINTMENT:{id}`-sourced consent grant for the appointment's doctor; declining it deactivates **only that** grant, leaving any manual grant (SR-008) or other-appointment grants untouched. The doctor's effective access is the union of all active grants. This is the per-source scoping that SR-036 requires to avoid a decline incorrectly stripping legitimately held access. Traces to SR-036 criteria 1, 3, 4 (Cases A/B/C), 5, 6, 7.

## Interfaces to honor

Composes over `AppointmentService.confirm/decline` (TASK-048) and `ConsentService` from [12-interfaces.md](../../design/12-interfaces.md) §12.1 **verbatim**:

```python
class ConsentService:
    def grant(self, patient_id: UUID, doctor_id: UUID, source: str) -> ConsentGrant: ...
    def revoke(self, grant_id: UUID | None = None, source: str | None = None) -> None: ...
    def list_grants(self, patient_id: UUID) -> list[ConsentGrant]: ...
```

- Confirm calls `grant(patient_id, doctor_id, source=f"APPOINTMENT:{appointment_id}")`; decline calls `revoke(source=f"APPOINTMENT:{appointment_id}")` — revoke is **scoped by source**, so it can only ever deactivate this appointment's grant (SR-036 AC-4). It **must not** revoke by `(doctor, patient)` pair (that would strip other grants — the explicit anti-pattern in SR-036 risk analysis).
- The grant is created **server-side** by the confirm event — never client-initiated, cannot be bypassed (SR-036 control measure / AC-1).
- Effective access is evaluated by `AuthorizationService.effective_access(doctor_id, patient_id)` as the **union** of active grants (§12.1, SR-036 AC-4); this unit only adds/removes the per-source grant, it does not re-implement the union.
- Grant + revoke run in the **same transaction** as the state transition (TASK-048) so state and consent never diverge.

## Implementation detail

- Files to modify:
  - `backend/app/appointments/service.py` — in `confirm`, after the transition, create the `APPOINTMENT:{id}` grant; in `decline`, revoke that source. Both within the existing transition transaction.
- Source convention: `ConsentGrant.source` string `APPOINTMENT:{appointment_id}` (vs. `MANUAL` for SR-008 grants). The per-source uniqueness means re-confirming would target the same source (idempotent grant) — but the state machine (TASK-048) already forbids re-confirming a declined appointment, so this is defensive.
- Grant lifetime: the appointment grant **persists after the appointment date/time passes** (SR-036 AC-5); it ends only on decline of that appointment, explicit SR-008 revoke, or account modification. This unit does not expire it by time.
- Audit (SR-036 AC-6): the grant/revoke records `consent.grant` / `consent.revoke` with patient identity, doctor identity, appointment id, trigger action (`appointment confirmed` / `appointment declined`), timestamp. (Distinct from the appointment-state audit of TASK-048; both are emitted.)
- Unified view (SR-036 AC-7): `GET /me/consents` ([api-design.md](../../specifications/api-design.md)) returns `list_grants(patient_id)` including both `MANUAL` and `APPOINTMENT:{id}` grants — no extra work here beyond ensuring the source label distinguishes them.
- Error cases: confirm/decline error handling is inherited from TASK-048; consent-side failures roll back the transition (transactional).
- Edge cases — the three decline cases (SR-036 AC-4), each a test:
  - **Case A** — doctor had no prior access: confirm creates grant; decline revokes it → access returns to none.
  - **Case B** — doctor already had a MANUAL grant (or a different appointment's grant): confirm adds the appointment grant; decline revokes only the appointment grant → doctor **retains** access via the other grant (effective_access stays true).
  - **Case C** — appointment never confirmed (still PENDING / previously DECLINED): decline finds no `APPOINTMENT:{id}` grant to revoke → no consent change (SR-036 AC-4 Case C). Also SR-036 AC-3: a PENDING/DECLINED appointment creates **no** grant.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/appointments/test_consent_link.py`):
  - patient confirms → `APPOINTMENT:{id}` grant created for the doctor; `effective_access(doctor, patient)` becomes true (SR-036 AC-1/AC-2).
  - while PENDING, no grant exists; doctor without other grants has no access (SR-036 AC-3).
  - **Case A:** no prior access → confirm → decline → `effective_access` false again (SR-036 AC-4 A).
  - **Case B:** pre-existing MANUAL grant → confirm → decline → MANUAL grant intact, `effective_access` still true (SR-036 AC-4 B). Assert the MANUAL grant row is untouched.
  - **Case B':** pre-existing grant from a *different* appointment → declining this appointment leaves the other appointment's grant active (SR-036 AC-4 B).
  - **Case C:** decline a never-confirmed (PENDING/previously-DECLINED) appointment → no grant to revoke, no consent change (SR-036 AC-4 C).
  - grant persists after `scheduled_at` is in the past (SR-036 AC-5).
  - grant created server-side by confirm, not accepted from client input (SR-036 AC-1 control).
  - confirm/decline emit `consent.grant`/`consent.revoke` audit with appointment id + trigger action (SR-036 AC-6).
  - `list_grants` / `GET /me/consents` shows manual and appointment grants together (SR-036 AC-7).
  - consent failure rolls back the state transition (transactional integrity).
- Integration (`backend/tests/api/test_appointment_consent_api.py`): confirm then a doctor `GET /patients/{id}/clinical-entries` succeeds; decline then the same fetch is denied (Case A), while a manually-granted doctor remains allowed (Case B).

## Acceptance criteria

- [x] Confirming an appointment creates an `APPOINTMENT:{id}` consent grant for the doctor, server-side (SR-036 AC-1).
- [x] After the grant the doctor can access the patient's clinical data without further patient action (SR-036 AC-2).
- [x] A PENDING or DECLINED appointment creates no grant (SR-036 AC-3).
- [x] Declining revokes only that appointment's grant — Cases A, B, C behave exactly as specified (SR-036 AC-4).
- [x] The appointment grant persists past the appointment datetime until explicit revoke/account change (SR-036 AC-5).
- [x] Every grant/revoke triggered by confirm/decline is audited with appointment id and trigger action (SR-036 AC-6).
- [x] The patient's consent view shows manual and appointment grants together (SR-036 AC-7).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit + integration tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (consent view reflects appointment grants)
- [x] Audit events emitted for security-relevant actions (SR-036 AC-6, SR-023)
- [x] Traceability matrix row updated (SR-036 → TASK-049 → tests)
- [x] Security review completed (consent / authorization-affecting code — SR-031.6)

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** AUDIT-FINDINGS.md (mock-only evidence). Unchecked acceptance-criteria / DoD items above reflect the gaps the audit found; this task stays **In Progress** until they are addressed.
