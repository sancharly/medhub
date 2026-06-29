# TASK-044 — Clinical entry create / list

- **Phase:** 3 — Domain services
- **Software item / unit:** SI-CLINICAL / U-CLIN-EntryCrud
- **Implements:** SR-012 (required fields, author from session, retrievable), SR-006 (doctor reads authorized patient), SR-007 (patient reads own); ADR-0004
- **Depends on:** TASK-027 (API deps / authz guard), TASK-014 (`AuthorizationService` / consent evaluation) — must be merged first
- **Branch:** `feature/clinical-entry`
- **Status:** In Progress (audit 2026-06-29)

## Objective

Let a doctor create a clinical entry bound to a patient with the required fields (date/time, patient, authoring doctor, description) — the authoring doctor taken from the authenticated session, not the client — and let authorized users list a patient's entries. All reads pass the central authorization check so a doctor sees only patients they are granted (SR-006) and a patient sees only their own record (SR-007). Traces to SR-012, SR-006, SR-007.

## Interfaces to honor

Implements `ClinicalDataService` from [12-interfaces.md](../../design/12-interfaces.md) §12.1 (provider SI-CLINICAL; consumers SI-API, SI-MOD-DICOM-BE via PlatformServices) **verbatim contract**:

```python
class ClinicalDataService:
    def list_entries(self, actor: Account, patient_id: UUID) -> list[ClinicalEntry]: ...   # pre-authorized
    def create_entry(self, actor: Account, patient_id: UUID,
                     occurred_at: datetime, description: str) -> ClinicalEntry: ...
    # author is set from `actor`, never from the request body (SR-012.3)
```

- Per §12.3 rule 1, this data item **must** call `AuthorizationService.authorize(actor, action, resource)` before returning or writing protected data — it never re-implements access checks. `create_entry` authorizes `clinical:create` for `(doctor → patient)`; `list_entries` authorizes `clinical:read` for `(actor → patient)`, which the policy resolves via the union of consent grants (manual + appointment, SR-036) for a doctor, or self-access for a patient (SR-007).
- The authoring doctor is **always** `actor` from the session; the service signature has no author parameter, so the client cannot spoof it (SR-012.3).
- Attachments are a separate unit (TASK-045/046); this unit returns entries and their attachment metadata refs only.

## Implementation detail

- Files to create:
  - `backend/app/clinical/service.py` — `ClinicalDataService` with `create_entry`, `list_entries`.
  - `backend/app/db/models/clinical_entry.py` — `ClinicalEntry`: `id` (UUID), `patient_id` (FK), `author_id` (FK, the doctor), `occurred_at` (datetime), `description` (text, non-empty), `created_at`. FHIR-aligned per [fhir-mapping.md](../../specifications/fhir-mapping.md) (SR-021); JSONB extension column for FHIR fields if the convention exists.
  - `backend/app/db/repositories/clinical_repository.py` — `add(entry)`, `list_for_patient(patient_id)` (parameterized, ordered by `occurred_at` desc).
  - `backend/app/api/schemas/clinical.py` — Pydantic v2 DTOs (camelCase): request `{ occurredAt, description }` (no author), response includes `id, patientId, authorId, occurredAt, description, attachments[]`.
  - `backend/app/db/alembic/versions/<rev>_clinical_entry.py` — migration.
- Endpoints (SI-API): `POST /patients/{id}/clinical-entries`, `GET /patients/{id}/clinical-entries` ([api-design.md](../../specifications/api-design.md)).
- Validation (Pydantic, authoritative server-side, SR-031.5): `occurredAt` required ISO-8601; `description` required, non-empty after trim; `patient_id` path param must reference an existing patient.
- Audit: clinical-data **access** (SR-023 AC-2) — `list_entries` records `clinical.read` with actor, target patient, outcome, and the authorization basis (manual/appointment, SR-006 AC-4); `create_entry` records `clinical.create`.
- Error cases (RFC 7807): missing `occurredAt`/`description` → `400 /errors/validation-error` with `errors[]` (SR-012 AC-2); non-existent patient → `404 /errors/not-found`; unauthorized doctor/patient → `403 /errors/forbidden`, no entries disclosed (SR-005, SR-006 AC-3, SR-007 AC-3); a non-doctor attempting create → `403`.
- Edge cases: a patient is **not** an author — only doctors create (policy). A doctor with no grant to the target patient is denied both read and create (SR-006 AC-3). Empty `description` (whitespace) is rejected (SR-012 AC-2). Author is set from `actor.id` regardless of any author-like field the client sends (SR-012 AC-3).

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/clinical/test_clinical_service.py`):
  - doctor with grant creates entry → persisted with `author_id == actor.id`, `occurred_at`, patient, description (SR-012 AC-1/AC-2).
  - request carrying a spoofed author field → stored author is the session doctor, not the client value (SR-012 AC-3).
  - missing `occurredAt` or blank `description` → validation error, nothing persisted (SR-012 AC-2).
  - doctor without grant `create_entry` / `list_entries` for that patient → denied 403, no data, denied access audited (SR-005, SR-006 AC-3).
  - doctor with grant `list_entries` → returns patient's entries; access audited with basis (SR-006 AC-2/AC-4).
  - patient `list_entries` on **own** record → returns own entries (SR-007 AC-2).
  - patient `list_entries` on **another** patient → denied 403 (SR-007 AC-3).
  - created entry retrievable in a later `list_entries` (SR-012 AC-4).
- Integration (`backend/tests/api/test_clinical_api.py`): create + list round-trip through routers + authz dependency; cross-patient access blocked with `problem+json`.

## Acceptance criteria

- [ ] A doctor can create an entry tied to a patient with date/time, patient, author, description (SR-012 AC-1/AC-2).
- [ ] An entry missing any required field is rejected (SR-012 AC-2).
- [ ] The authoring doctor is set from the session and cannot be spoofed by the client (SR-012 AC-3).
- [ ] A saved entry is retrievable as part of the patient's history by authorized users (SR-012 AC-4).
- [ ] A doctor can list entries only for patients they are authorized for; others denied (SR-006 AC-2/AC-3).
- [ ] A patient can list only their own entries (SR-007 AC-2/AC-3).
- [ ] Clinical-data access and creation are audited with basis (SR-023 AC-2, SR-006 AC-4).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit + integration tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (clinical-entry endpoints)
- [ ] Audit events emitted for security-relevant actions (SR-023)
- [ ] Traceability matrix row updated (SR-012, SR-006, SR-007 → TASK-044 → tests)
- [ ] Security review N/A (authz consumed, not implemented here)

## Audit verdict (2026-06-29)

- **Verdict:** FAIL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-044a. Unchecked acceptance-criteria / DoD items above reflect the gaps the audit found; this task stays **In Progress** until they are addressed.
