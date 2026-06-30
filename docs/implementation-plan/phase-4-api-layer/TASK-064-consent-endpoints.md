# TASK-064 — Consent endpoints

- **Phase:** 4 — API layer
- **Software item / unit:** SI-API / U-API-Routers, U-API-DTO
- **Implements:** SR-008 (patient grants/revokes a doctor, immediate effect, audited);
  SR-036.7 (unified view of all grants — manual + appointment-derived)
- **Depends on:** TASK-028 (ConsentService) — must be merged first
- **Branch:** `feature/consent-endpoints`
- **Status:** Completed

## Objective

Expose the SI-AUTHZ consent HTTP surface: a patient grants a named doctor manual access to their
clinical data (`POST /consents`), revokes it with immediate effect (`DELETE /consents/{id}`), and
views a unified list of all active grants — manual plus appointment-confirmation-derived
(`GET /me/consents`). Routers delegate to `ConsentService`; the current consent state is the input
the `AuthorizationService` reads, so a revoke takes effect on the doctor's next request. Traces to
SR-008, SR-036.7.

## Interfaces to honor

HTTP contract (verbatim from [api-design.md](../../specifications/api-design.md)):

| Method & path           | Purpose                                           | Key reqs   |
|-------------------------|---------------------------------------------------|------------|
| `POST /consents`        | patient grants a doctor (MANUAL)                  | SR-008.1   |
| `DELETE /consents/{id}` | patient revokes (immediate)                       | SR-008.3/4 |
| `GET /me/consents`      | unified view of all grants (manual + appointment) | SR-036.7   |

Consumes ([12-interfaces.md](../../design/12-interfaces.md) §12.1) **verbatim**:

```python
ConsentService.grant(self, patient_id: UUID, doctor_id: UUID, source: GrantSource) -> ConsentGrant  # TASK-028
ConsentService.revoke(self, grant_id: UUID) -> None                                                 # TASK-028
ConsentService.list_grants(self, patient_id: UUID) -> list[ConsentGrant]                            # TASK-028
```

All endpoints declare the `require(action, resource_loader)` guard (TASK-025). `POST`/`DELETE` are
**patient-only** on the caller's **own** consents (the actor is the authenticated patient; the
doctor is the grant target). `GET /me/consents` is scoped to the calling patient. `source` is
`MANUAL` for this endpoint; appointment-derived grants (`APPOINTMENT:{id}`) are created/revoked by
SI-APPT (TASK-049), not here, but **appear** in the unified `GET /me/consents` list (SR-036.7).

Must **not**: let a doctor or admin grant/revoke on a patient's behalf (consent is the patient's
action, SR-008); revoke an appointment-derived grant via `DELETE /consents/{id}` in a way that
diverges from SR-036.4 — manual revoke removes the manual grant only; the doctor's effective access
is the **union** of remaining active grants (SR-036.7, ADR-0006); re-implement the union/effective
access (that is `AuthorizationService.effective_access`, TASK-027).

## Implementation detail

- Files to create:
  - `backend/app/api/routers/consents.py` — `APIRouter(prefix="/consents")` (grant/revoke) +
    `GET /me/consents` (mounted alongside the `/me` router, TASK-067, or under `/api/v1`).
  - `backend/app/api/schemas/consent.py` — Pydantic v2 DTOs (camelCase):
    - `ConsentGrantRequest { doctorId: UUID }`
    - `ConsentGrantResponse { id, doctorId, source, createdAt }`
      (`source` ∈ `MANUAL | APPOINTMENT`)
    - `ConsentListResponse { items: list[ConsentGrantResponse] }` (unified manual + appointment)
- `POST /consents` (patient only, CSRF-checked): authorize `consent:grant` for the calling patient;
  `ConsentService.grant(patient_id=current_user.id, doctor_id=body.doctorId, source=MANUAL)`. The
  `doctorId` must reference an existing doctor account. 201 `ConsentGrantResponse`. After the grant,
  the doctor can view that patient's clinical data subject to SR-006 (SR-008.2). Audit
  `CONSENT_GRANT` with patient, doctor, timestamp (SR-008.5).
- `DELETE /consents/{id}` (patient only, CSRF-checked): authorize `consent:revoke` — the grant must
  belong to the calling patient; `ConsentService.revoke(id)`. Effect is **immediate**: the next
  request by that doctor is denied if no other active grant remains (SR-008.3/4, evaluated by the
  AuthorizationService union, SR-036.4). 204. Audit `CONSENT_REVOKE` (SR-008.5).
- `GET /me/consents` (patient): authorize `consent:list_own`; `ConsentService.list_grants(current_user.id)`
  returns the **unified** set — manual grants and appointment-confirmation grants alike — so the
  patient sees a complete picture of who has access (SR-036.7). 200 `ConsentListResponse`.
- Edge cases: revoking a non-existent or another patient's grant id → 404 (no enumeration of other
  patients' grants); granting a doctor who already holds an active manual grant is idempotent / 409
  per ConsentService policy (TASK-028).
- Error cases (RFC 7807, base `https://medhub.example/errors/`): missing/invalid `doctorId` →
  `400 /errors/validation-error`; `doctorId` not a doctor → `400`; caller not the owning patient,
  or a doctor/admin attempting grant/revoke → `403 /errors/forbidden`; absent grant or one not
  visible to the caller → `404 /errors/not-found`.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/api/test_consents_router.py`):
  - patient grants a named doctor → 201; the doctor can then read the patient's data subject to
    SR-006 (SR-008.1/2).
  - patient revokes → 204; a subsequent read by that doctor is denied **immediately** when no other
    grant remains (SR-008.3/4).
  - a doctor or admin attempting `POST`/`DELETE` on a patient's consents → 403 (SR-008, patient-only).
  - `GET /me/consents` returns manual + appointment-derived grants in one unified list (SR-036.7).
  - revoking a manual grant does not remove an appointment-derived grant for the same doctor; the
    doctor retains access via the appointment grant (SR-036.4 Case B, union semantics).
  - `doctorId` referencing a non-doctor → 400; revoke of another patient's grant → 404.
  - grant/revoke audited with patient, doctor, timestamp (SR-008.5).
  - state-changing endpoints reject a missing CSRF token → 403 (SR-031.3).
- Integration (`backend/tests/api/test_consent_integration.py`): grant → doctor reads clinical entry
  → revoke → doctor read denied, end-to-end through the test client.

## Acceptance criteria

- [x] A patient can grant a named doctor access to their clinical data (SR-008.1).
- [x] After a grant, the doctor can view that patient's data subject to SR-006 (SR-008.2).
- [x] A patient can revoke a grant; the effect is immediate on the doctor's next request (SR-008.3/4).
- [x] Only the owning patient can grant/revoke; doctors/admins cannot act on their behalf (SR-008).
- [x] `GET /me/consents` shows a unified view of manual + appointment-derived grants (SR-036.7).
- [x] Manual revoke removes only the manual grant; union of remaining grants determines access (SR-036.4).
- [x] Grant and revoke are audited; state-changing requests are CSRF-protected (SR-008.5, SR-031.3). (TASK-069a)

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit + integration tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (three endpoints + DTOs)
- [x] Audit events emitted for security-relevant actions (consent grant/revoke — SR-008.5, SR-023)
- [x] Traceability matrix row updated (SR-008, SR-036.7 → TASK-064 → tests)
- [x] Security review N/A (authz/consent service consumed, not implemented here)

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL (CSRF gap — resolved by TASK-069a)
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-069a completed. All AC/DoD items now satisfied.

## QA sign-off

- **Date:** 2026-06-30
- **Reviewer:** QA Engineer agent (phase-4 audit remediation)
- **Evidence:** CSRF gap closed by TASK-069a; OpenAPI regenerated in TASK-068a; 484 tests pass (ruff + mypy clean).
