# TASK-028 — ConsentService + effective_access union

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-AUTHZ / U-AUTHZ-Consent
- **Implements:** SR-008 (patient grant/revoke, immediate), SR-036 (per-source grants, union =
  effective access); ADR-0006
- **Depends on:** TASK-027 (AuthorizationService — the consumer of the union)
- **Branch:** `feature/consent-service`
- **Status:** Completed

## Objective

Model patient consent as **per-source `ConsentGrant` rows** and compute a doctor's effective
clinical access as the **union of active grants** (ADR-0006, SR-036). Provide transactional,
immediate grant/revoke so a manual revoke (SR-008) or an appointment decline (SR-036, wired in
TASK-049) deactivates **only the matching row**, leaving other grants intact. This supplies the
consent input that `AuthorizationService.effective_access` reads live on every request, making
SR-008 AC-4 immediacy and the SR-036 Case A/B/C decline semantics fall out naturally.

## Interfaces to honor

Provided interface (from [12-interfaces.md](../../design/12-interfaces.md), SI-AUTHZ
`ConsentService`), signatures verbatim:

```python
class ConsentService:
    def grant(self, patient_id, doctor_id, source) -> ConsentGrant: ...
    def revoke(self, grant_id_or_source) -> None: ...     # revoke(grant_id | source)
    def list_grants(self, patient_id) -> list[ConsentGrant]: ...
```

Plus the union predicate consumed by `AuthorizationService` (TASK-027):

```python
def has_active_grant(self, doctor_id, patient_id) -> bool: ...   # EXISTS(active ConsentGrant for the pair)
```

`source ∈ {MANUAL, APPOINTMENT:{appointment_id}}` (ADR-0006). Consumers: SI-APPT (TASK-049),
SI-API consent endpoints (TASK-064), SI-AUTHZ (TASK-027). Consumes `AuditService` (TASK-014).

Must **not**: collapse grants to a single boolean per pair (explicitly rejected, SR-036 AC-4
control measure / ADR-0006 alternatives); let a decline revoke any row other than the matching
`APPOINTMENT:{id}` (SR-036 AC-4); defer the effect (revoke is immediate & transactional, SR-008 AC-4).

## Implementation detail

- Files to create:
  - `backend/app/authz/consent.py` — `ConsentService`, `ConsentSource` value type.
- Data model (`ConsentGrant`, model/migration in TASK-010/011; this task adds the repository
  methods if missing): row `(id, patient_id, doctor_id, source, active, created_at,
  deactivated_at)`. Index `(patient_id, doctor_id, active)` for the union query (ADR-0006 perf).
  Partial-unique on `(patient_id, doctor_id, source) WHERE active` so the same source is not
  duplicated.
- `grant(patient_id, doctor_id, source)`: idempotently create/activate the row for that source;
  transactional; audit `CONSENT_GRANTED` with patient, doctor, source, ts (SR-008 AC-5, SR-036 AC-6).
- `revoke(grant_id_or_source)`: accept either a grant id or a `(patient, doctor, source)` selector;
  set `active=False`, `deactivated_at=now` on **only** the matching row, transactionally; audit
  `CONSENT_REVOKED` (SR-008 AC-5, SR-036 AC-6). Manual revoke (SR-008.3) targets the `MANUAL` row;
  decline (SR-036, TASK-049) targets `APPOINTMENT:{id}`.
- `has_active_grant`: `EXISTS` over active rows for the pair — the union (SR-036 AC-3/AC-4).
- `list_grants(patient_id)`: all grants (active + the unified manual+appointment view feeding
  `GET /me/consents`, SR-036 AC-7) for the patient's complete picture.
- SR-036 decline cases verified end-to-end with TASK-049, but the **scoping** is this unit's
  responsibility: revoke removes exactly one source's contribution (Cases A/B/C).
- Confirmation requirement for manual revoke is a UI/endpoint concern (SR-008 control measure via
  SR-027.2, TASK-064/094); the service performs the deactivation.
- Error cases: revoking a non-existent/foreign grant → `NotFoundError` (404) at the endpoint
  (TASK-064); a patient revoking another patient's grant is denied by `AuthorizationService`
  (TASK-027) before reaching this service.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/authz/test_consent_service.py`):
  - `grant(MANUAL)` then `has_active_grant` True; `revoke(MANUAL)` → False, immediately (SR-008 AC-2/4).
  - Union: a MANUAL grant **and** an `APPOINTMENT:{id}` grant both active → `has_active_grant` True;
    declining the appointment (`revoke(APPOINTMENT:{id})`) leaves MANUAL active → still True
    (SR-036 Case B) (SR-036 AC-3/AC-4).
  - SR-036 Case A: only an `APPOINTMENT:{id}` grant; revoke it → `has_active_grant` False.
  - SR-036 Case C: revoke for an appointment that was never confirmed (no row) → no-op, no error,
    other grants untouched.
  - `revoke` deactivates **only** the matching row; assert sibling rows' `active` unchanged
    (SR-036 AC-4 control measure).
  - Every grant and revoke writes an audit record with patient, doctor, source/appointment, ts
    (SR-008 AC-5, SR-036 AC-6).
  - `list_grants` returns the unified manual + appointment view (SR-036 AC-7).
- Integration (`backend/tests/authz/test_consent_repo.py`): partial-unique constraint and the
  indexed union query verified against the real DB (crosses SI-PERSIST).

## Acceptance criteria

Distilled from SR-008 / SR-036:

- [ ] Patient can grant a named doctor (MANUAL) and the doctor then has access (SR-008 AC-1/AC-2).
- [ ] Revoke takes effect immediately on the next request (SR-008 AC-3/AC-4).
- [ ] Grants are per-source; effective access = union of active grants (SR-036 AC-3).
- [ ] Decline revokes only that appointment's grant — Cases A/B/C correct (SR-036 AC-4).
- [ ] Each grant/revoke audited with patient, doctor, source/appointment id, ts (SR-008 AC-5, SR-036 AC-6).
- [ ] Unified manual + appointment grant view available to the patient (SR-036 AC-7).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit (and required integration) tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (consent endpoints land in TASK-064)
- [ ] Audit events emitted for security-relevant actions (CONSENT_GRANTED / CONSENT_REVOKED — SR-023)
- [ ] Traceability matrix row updated (SR-008, SR-036, ADR-0006 → TASK-028 → tests)
- [ ] Security review completed (auth/session/authz task — SR-031.6)
