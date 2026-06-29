# TASK-066a — Attachment upload via multipart + streaming (remediation)

- **Phase:** 4 — API layer
- **Implements / restores:** SR-013; remediates TASK-066, TASK-045
- **Depends on:** TASK-066, TASK-045
- **Branch:** `feature/multipart-upload`
- **Status:** Not started
- **Source:** `AUDIT-LEDGER.md` — TASK-066 verdict **FAIL** (contract deviation)

## Objective

The attachment upload endpoint reads a raw request body + an `X-Filename` header instead of the
contract's `multipart/form-data`, and both upload and fetch buffer the whole object in memory. Also the
DICOM metadata produced by `validate_dicom` is discarded rather than stored.

## Implementation detail

- Change `POST /clinical-entries/{id}/attachments` to accept `multipart/form-data` (FastAPI `UploadFile`),
  per `api-design.md`; update the frontend `uploadAttachment` accordingly.
- Persist the DICOM-derived metadata (e.g. modality) returned by `validate_dicom` (`app/attachments/service.py`).
- Stream object bytes on upload and fetch rather than buffering the whole file (SR-026 budget).

## Acceptance criteria

- [ ] Upload accepts standard multipart form-data (incl. valid DICOM) and the frontend uses it.
- [ ] DICOM metadata (modality) is stored with the attachment.
- [ ] Large files stream (no full in-memory buffering) on upload and download.
- [ ] Invalid DICOM still rejected; no orphaned objects.

## Definition of Done

- [ ] Lint + type-check pass
- [ ] Unit/integration tests incl. a real DICOM fixture + multipart
- [ ] OpenAPI regenerated (multipart request body documented) + frontend types regenerated
- [ ] Traceability row updated (SR-013 → TASK-066a → tests)
- [ ] Security review completed (authz before bytes preserved)
