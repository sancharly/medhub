# TASK-066 — Clinical-entry & attachment endpoints

- **Phase:** 4 — API layer
- **Software item / unit:** SI-API / U-API-Routers, U-API-DTO
- **Implements:** SR-012 (doctor creates a clinical entry, required fields, author from session,
  authorized list); SR-013 (file attachments incl. DICOM, bound to entry/patient, authorized
  retrieval, encrypted at rest); SR-005 (deny-by-default authorization on every clinical/attachment
  request)
- **Depends on:** TASK-044 (clinical entry), TASK-045 (attachment upload), TASK-046 (attachment
  fetch) — must be merged first
- **Branch:** `feature/clinical-attachment-endpoints`
- **Status:** COMMITTED on `feature/phase-4` (commit ae0f5ff)

## Objective

Expose the SI-CLINICAL and SI-ATTACH HTTP surface: list a patient's clinical history
(`GET /patients/{id}/clinical-entries`), a doctor creates an entry with the author taken from the
session (`POST /patients/{id}/clinical-entries`), upload an attachment incl. DICOM
(`POST /clinical-entries/{id}/attachments`), and authorized download/stream
(`GET /attachments/{id}`). Every endpoint passes the `AuthorizationService` guard (deny-by-default,
SR-005); the authoring doctor is never client-supplied (SR-012.3). Traces to SR-012, SR-013, SR-005.

## Interfaces to honor

HTTP contract (verbatim from [api-design.md](../../specifications/api-design.md)):

| Method & path                             | Purpose                                    | Key reqs                 |
|-------------------------------------------|--------------------------------------------|--------------------------|
| `GET /patients/{id}/clinical-entries`     | list patient history (authz)               | SR-006, SR-007           |
| `POST /patients/{id}/clinical-entries`    | doctor creates entry (author from session) | SR-012                   |
| `POST /clinical-entries/{id}/attachments` | upload file (DICOM/report)                 | SR-013                   |
| `GET /attachments/{id}`                   | authorized download/stream                 | SR-005, SR-013.3, SR-022 |

Consumes ([12-interfaces.md](../../design/12-interfaces.md) §12.1) **verbatim**:

```python
ClinicalDataService.list_entries(self, patient_id: UUID) -> list[ClinicalEntry]   # TASK-044 (pre-authorized)
ClinicalDataService.create_entry(self, ...) -> ClinicalEntry                      # TASK-044 (author from session)
AttachmentService.store(self, entry_id: UUID, file) -> Attachment                 # TASK-045
AttachmentService.open(self, attachment_id: UUID) -> stream                       # TASK-046 (authorized)
```

All endpoints declare the `require(action, resource_loader)` guard (TASK-025); the resource loader
loads the patient / entry / attachment so the `AuthorizationService` (TASK-027) decides on the real
resource (deny-by-default, SR-005). The authoring doctor is set from `get_current_user`, never the
body (SR-012.3).

Must **not**: trust a client-supplied author/patient on create — author from session, patient from
the path (SR-012.3); return clinical data or attachment bytes before the authorization guard
allows (SR-005 AC-1/2/4); re-implement the consent/relationship check (it is the central
`AuthorizationService`, ADR-0006); stream attachment bytes through the DB path (object storage via
SI-ATTACH only, §8.9).

## Implementation detail

- Files to create:
  - `backend/app/api/routers/clinical.py` — `APIRouter` for `/patients/{id}/clinical-entries`
    (list/create) and `/clinical-entries/{id}/attachments` (upload); mounted under `/api/v1`.
  - `backend/app/api/routers/attachments.py` — `APIRouter(prefix="/attachments")` `GET /{id}` stream.
  - `backend/app/api/schemas/clinical.py` — Pydantic v2 DTOs (camelCase):
    - `ClinicalEntryCreateRequest { description: str, recordedAt: datetime | None }`
      (patient comes from the path; authoring doctor from the session — **not** in the body, SR-012.3)
    - `ClinicalEntryResponse { id, patientId, authorDoctorId, recordedAt, description, attachments: list[AttachmentSummary] }`
    - `AttachmentSummary { id, filename, contentType, sizeBytes }`
    - `ClinicalEntryListResponse { items: list[ClinicalEntryResponse], nextCursor: str | None }`
      (paginated, access-scoped)
- `GET /patients/{id}/clinical-entries` (authorized): authorize `clinical:read` with the patient as
  resource — the AuthorizationService grants only via an active consent/relationship (SR-006) or the
  patient viewing their own history (SR-007); `ClinicalDataService.list_entries(patientId)`;
  paginated. Reads are audited (clinical-data access, SR-023, §8.4).
- `POST /patients/{id}/clinical-entries` (doctor only, CSRF-checked): authorize `clinical:create`
  with the patient as resource; `create_entry` records date/time, patient (from path), **authoring
  doctor from the session** (SR-012.3), and description; rejects a missing required field
  (SR-012.2). 201 `ClinicalEntryResponse`. Audit `CLINICAL_ENTRY_CREATE`.
- `POST /clinical-entries/{id}/attachments` (doctor only, CSRF-checked): authorize
  `attachment:create` with the entry (→ its patient) as resource; `multipart/form-data` upload;
  `AttachmentService.store(entryId, file)` validates and stores the object with SSE encryption at
  rest (SR-013.4, SR-022) and binds it transactionally to the entry and thereby the patient
  (SR-013.2); accepts DICOM among other formats (SR-013.1). 201 `AttachmentSummary`. Audit.
- `GET /attachments/{id}` (authorized): authorize `attachment:read` with the attachment (→ its
  entry → patient) as resource (SR-005, SR-013.3); `AttachmentService.open(id)` streams the bytes
  (or issues a scoped pre-signed URL per TASK-046) with the correct `Content-Type`; reads audited.
- Edge cases: an upload to an entry the caller cannot access → 403 before any storage write; a
  download for an attachment of a patient the caller lost consent to → 403 (immediate, SR-008.4);
  unknown patient/entry/attachment id → 404.
- Error cases (RFC 7807, base `https://medhub.example/errors/`): missing `description` →
  `400 /errors/validation-error` (SR-012.2); author/patient spoofing attempt in the body is ignored
  (author from session, SR-012.3); authorization denied → `403 /errors/forbidden` (no protected
  data, SR-005 AC-4); absent resource → `404 /errors/not-found`.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/api/test_clinical_router.py`):
  - doctor with access creates an entry → 201, author = session user (a body-supplied author is
    ignored), required fields enforced (SR-012.2/3).
  - missing `description` → 400 (SR-012.2).
  - a doctor **without** an active grant listing/creating for that patient → 403 (deny-by-default,
    SR-005, SR-006).
  - patient lists **their own** history → 200 (SR-007); a patient listing another patient → 403.
  - clinical reads/creates are audited (clinical-data access, SR-023).
- Unit (`backend/tests/api/test_attachments_router.py`):
  - doctor with access uploads a DICOM file → 201, bound to entry+patient, stored with SSE
    (SR-013.1/2/4).
  - authorized `GET /attachments/{id}` streams the bytes with the right content type (SR-013.3).
  - unauthorized download (no grant) → 403 before any byte is returned (SR-005, SR-013.3).
  - upload to an entry the caller cannot access → 403, nothing stored.
  - state-changing endpoints reject a missing CSRF token → 403 (SR-031.3).
- Integration (`backend/tests/api/test_clinical_attachment_integration.py`): create entry → upload
  attachment → authorized download succeeds → revoke consent → download now 403, end-to-end.

## Acceptance criteria

- [ ] A doctor can create a clinical entry for a patient; required fields enforced (SR-012.1/2).
- [ ] The authoring doctor is taken from the session and cannot be spoofed by the client (SR-012.3).
- [ ] A saved entry is retrievable as part of the patient's history by authorized users (SR-012.4).
- [ ] A doctor can attach one or more files incl. DICOM, bound to entry+patient (SR-013.1/2).
- [ ] An authorized user can download/open an attachment; attachments are encrypted at rest (SR-013.3/4, SR-022).
- [ ] Every clinical/attachment request passes the deny-by-default authorization guard (SR-005); reads are audited (SR-023).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit + integration tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (four endpoints + DTOs; multipart upload documented)
- [ ] Audit events emitted for security-relevant actions (clinical read/create, attachment read/store — SR-023)
- [ ] Traceability matrix row updated (SR-012, SR-013, SR-005 → TASK-066 → tests)
- [ ] Security review N/A (authz consumed, not implemented here; but verify no bytes precede the authz guard)
