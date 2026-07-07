---
id: "TASK-045"
type: task
title: "Attachment upload → MinIO + pydicom validation"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-013"
    relation: implements
  - target: "SR-022"
    relation: implements
  - target: "TASK-044"
    relation: relates_to
  - target: "TASK-013"
    relation: relates_to
tags: ["phase:3-domain-services"]
---

- **Phase:** 3 — Domain services
- **Software item / unit:** SI-ATTACH / U-ATT-Upload
- **Implements:** SR-013 (AC-1 attach incl. DICOM, AC-2 bound to entry/patient, AC-4 encrypted at rest), SR-022 (AC-2 AES-256 at rest); ADR-0009, ADR-0008
- **Depends on:** TASK-044 (clinical entry), TASK-013 (object-storage / MinIO client + bucket config) — must be merged first
- **Branch:** `feature/attachment-upload`
- **Status:** Completed

## Objective

Let a doctor attach one or more files (DICOM images, reports, analysis results) to a clinical entry. The binary is stored as an encrypted object in MinIO (SSE-AES256); only `Attachment` metadata lives in PostgreSQL. The object write and the metadata row are bound transactionally to the entry — and thereby the patient — so an attachment can never be orphaned or mis-attributed. DICOM files are validated with `pydicom` on upload. Traces to SR-013 AC-1/AC-2/AC-4 and SR-022 AC-2.

## Interfaces to honor

Implements the write half of `AttachmentService` from [12-interfaces.md](../../design/12-interfaces.md) §12.1 (provider SI-ATTACH) **verbatim**:

```python
class AttachmentService:
    def store(self, actor: Account, entry_id: UUID, file: UploadFile) -> Attachment: ...   # authorized
    # open(...) is TASK-046
```

- Per §12.3 rule 1, `store` authorizes via `AuthorizationService.authorize(actor, "clinical:write", entry.patient)` before writing — only a doctor authorized to that entry's patient may attach (SR-005). Deny-by-default.
- Per §12.3 rule 3, **only SI-ATTACH talks to object storage**; no other item holds bucket credentials (ADR-0009). The SPA/module never gets direct bucket access.
- Validation/content rules are server-side authoritative (SR-031.5).

## Implementation detail

- Files to create:
  - `backend/app/attachments/service.py` — `AttachmentService.store`.
  - `backend/app/attachments/dicom_validation.py` — `validate_dicom(bytes) -> DicomSummary` using **`pydicom`** (`dcmread`): confirm it parses as DICOM Part-10, extract `Modality`, `SOPClassUID`, `Rows/Columns`, number of frames/instances for metadata. Reject unparseable files declared as DICOM.
  - `backend/app/db/models/attachment.py` — `Attachment` (per ADR-0009): `id`, `clinical_entry_id` (FK), `patient_id` (denormalized FK for authz scoping), `filename`, `content_type`, `size`, `storage_key`, `checksum` (sha-256), `created_at`. (DICOM-derived fields, e.g. `modality`, stored in a JSONB metadata column.)
  - `backend/app/db/repositories/attachment_repository.py` — `add(attachment)`.
  - `backend/app/core/object_storage.py` — extend the TASK-013 MinIO client with `put_object(key, stream, length, content_type, sse=AES256)` if not already present (surgical).
  - `backend/app/db/alembic/versions/<rev>_attachment.py` — migration.
- Endpoint (SI-API): `POST /clinical-entries/{id}/attachments` (multipart) ([api-design.md](../../specifications/api-design.md)). Supports one-or-more files (SR-013 AC-1) — repeat the field per file.
- Storage: write the object **first** with **SSE AES-256** (`x-amz-server-side-encryption: AES256` on the MinIO bucket per ADR-0009 / SR-022 AC-2), then commit the metadata row; on metadata-commit failure the orphaned object is cleaned (ADR-0009 cross-store consistency note). Compute and store the checksum.
- Validation: content type / size limits (config keys `ATTACHMENT_MAX_BYTES`, allowed types). For `application/dicom` (or `.dcm`), run `validate_dicom`; a file that fails to parse is rejected (SR-013 — "accepts DICOM image files" requires they are valid DICOM).
- Config keys (12-factor, NFR-007): `OBJECT_STORAGE_BUCKET`, `OBJECT_STORAGE_ENDPOINT`, credentials (env-injected), `ATTACHMENT_MAX_BYTES`.
- Audit: record `attachment.upload` with actor, entry/patient target, storage key (SR-023).
- Error cases (RFC 7807): unauthorized → `403 /errors/forbidden`; entry not found → `404 /errors/not-found`; oversize / disallowed type → `400 /errors/validation-error`; declared-DICOM-but-unparseable → `400 /errors/validation-error`.
- Edge cases: object write succeeds but DB commit fails → object is deleted (no orphan); DB row never references a missing object. `patient_id` is copied from the parent entry, not the client, so an attachment cannot be re-pointed to another patient (SR-013 AC-2). Multiple files in one request each get their own `Attachment` row + object.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/attachments/test_attachment_upload.py`, MinIO + pydicom faked/containerized):
  - authorized doctor uploads a report → object stored with SSE-AES256 header, metadata row bound to entry & patient, checksum set (SR-013 AC-1/AC-2/AC-4, SR-022 AC-2).
  - upload a valid DICOM → `pydicom` parses, modality captured, stored (SR-013 AC-1).
  - upload a file declared DICOM but corrupt → `400 validation-error`, nothing stored (validation).
  - multiple files in one request → multiple attachments, each bound to the entry (SR-013 AC-1).
  - oversize / disallowed type → `400`, nothing stored.
  - unauthorized doctor → `403`, no object/row written, denied access audited (SR-005, SR-023).
  - object stored but metadata commit fails → object cleaned up, no orphan (ADR-0009).
  - `patient_id` always taken from the entry, never the request (SR-013 AC-2).
  - upload audited (SR-023).
- Integration (`backend/tests/api/test_attachment_upload_api.py`): multipart upload through router + authz, against a MinIO test container; assert SSE on the stored object.

## Acceptance criteria

- [x] A doctor can attach one or more files, including valid DICOM, to a clinical entry (SR-013 AC-1).
- [x] Each attachment is bound to its entry and the entry's patient; patient is derived server-side (SR-013 AC-2).
- [x] Objects are stored in MinIO with server-side AES-256 encryption at rest (SR-013 AC-4, SR-022 AC-2).
- [x] DICOM files are validated with `pydicom`; invalid DICOM is rejected.
- [x] Object and metadata are written consistently; no orphaned object or dangling row (ADR-0009).
- [x] Upload restricted to authorized doctors and audited (SR-005, SR-023).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit + integration tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (upload endpoint)
- [x] Audit events emitted for security-relevant actions (SR-023)
- [x] Traceability matrix row updated (SR-013, SR-022 → TASK-045 → tests)
- [x] Security review N/A (authz consumed, not implemented here; storage-encryption config covered in TASK-045 review notes)

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-066a / AUDIT-FINDINGS.md. Unchecked acceptance-criteria / DoD items above reflect the gaps the audit found; this task stays **In Progress** until they are addressed.
