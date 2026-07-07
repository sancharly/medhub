---
id: "TASK-126"
type: task
title: "Attachment listing endpoint + clinical entry author name (remediation)"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-012"
    relation: implements
  - target: "SR-013"
    relation: implements
  - target: "TASK-066"
    relation: relates_to
  - target: "TASK-092"
    relation: relates_to
  - target: "TASK-132"
    relation: relates_to
  - target: "TASK-125"
    relation: relates_to
tags: ["phase:4-api-layer", "remediation-of:TASK-066", "original-id:TASK-066b"]
---

- **Phase:** 4 — API layer
- **Implements / restores:** SR-012, SR-013; remediates TASK-066, TASK-092/TASK-092a
- **Depends on:** TASK-066, TASK-066a
- **Branch:** `fix/phase-7-audit`
- **Status:** Completed
- **Source:** TASK-092/TASK-092a frontend remediation (2026-06-30) — flagged two real backend gaps
  blocking honest completion of their AC

*Originally filed as TASK-066b.*

## Objective

The phase-7 frontend remediation (TASK-092a) closed its frontend-only gaps but documented two backend
gaps it could not solve within its own scope:

1. There is no endpoint to list attachments for a clinical entry. The backend only exposed
   `POST /clinical-entries/{entry_id}/attachments` (upload) and `GET /attachments/{attachment_id}`
   (fetch one, by id). The frontend faked attachment listing by caching upload responses
   client-side in TanStack Query, so attachments disappeared on page reload — violating SR-013 AC-3
   ("An authorized user can open/download an attachment").
2. `ClinicalEntryResponse` only exposed `author_id` (a UUID), not a human-readable name. The frontend
   could only resolve the author's name when the viewer *was* the author (via `GET /me`), falling back
   to the generic label "Doctor" for every other case — incomplete for SR-012 ("The UI shows the
   author returned by the server, read-only").

## Implementation detail

- `backend/app/attachments/service.py`: added `AttachmentService.list_attachments(actor, entry_id)` —
  looks up the clinical entry via `ClinicalRepository.get`, 404s if missing, authorizes
  `"clinical:read"` on an `attachment` resource scoped to the entry's `patient_id` (mirrors `open()`),
  audits `ATTACHMENT_ACCESS`, then returns `AttachmentRepository.list_for_clinical_entry(entry_id)`.
- `backend/app/api/routers/attachments.py`: added `GET /clinical-entries/{entry_id}/attachments`,
  `response_model=list[AttachmentResponse]`, calling the new service method.
- `backend/app/api/schemas/clinical.py`: added `author_name: str` to `ClinicalEntryResponse`.
- `backend/app/api/routers/clinical.py`: added a `_get_account_repo` dependency and an `_author_name`
  helper (`"{first_name} {surname}"`, or just `first_name` when `surname` is null). Both
  `create_clinical_entry` and `list_clinical_entries` now look up the author `Account` via
  `AccountRepository.get_by_id` and populate `authorName`. `list_clinical_entries` batches the author
  lookups by distinct `author_doctor_id` to avoid one query per entry.
- OpenAPI regenerated (`uv run python -m app.export_openapi --output openapi/openapi.json`); frontend
  types regenerated (`npm run generate:types`).

### Frontend wiring

- `frontend/src/api/client.ts`: added `listAttachments(entryId)` → `GET /clinical-entries/{entryId}/attachments`.
- `frontend/src/core/clinical/ClinicalEntryList.tsx`: `EntryAttachments` now uses
  `useQuery(['attachments', entryId], () => apiClient.listAttachments(entryId))` instead of a
  cache-only stub, so attachments persist across reloads. `EntryAuthor` is removed; the entry list
  renders `entry.authorName` directly from the server response.
- `frontend/src/core/clinical/AttachmentUpload.tsx`: the upload mutation's `onSuccess` now invalidates
  the `['attachments', entryId]` query instead of manually pushing into the TanStack Query cache.
- `frontend/src/core/clinical/ClinicalEntriesPage.test.tsx`: MSW mocks updated to serve
  `GET /clinical-entries/{entryId}/attachments` and to include `authorName` on entry fixtures, matching
  the real contract.

## Acceptance criteria

- [x] `GET /clinical-entries/{entry_id}/attachments` returns the attachments for that entry,
  authorized the same way as a single-attachment fetch (`clinical:read`, consent-gated).
- [x] A non-authorized actor (no consent) gets `403`; a non-existent entry gets `404`.
- [x] `ClinicalEntryResponse` includes `authorName` for every entry, populated server-side from the
  authoring doctor's `Account`, for both `create` and `list` responses.
- [x] Frontend attachment list persists across page reloads (no longer client-cache-only).
- [x] Frontend shows the real author name for any author, not just the viewer.

## Definition of Done

- [x] Lint + type-check pass (backend: ruff, mypy; frontend: eslint, tsc)
- [x] Backend unit/integration tests added: `tests/attachments/test_attachment_fetch.py`
      (`list_attachments` service tests — found, not-found, denied, audited),
      `tests/api/test_attachments_router.py` (`TestListAttachments`),
      `tests/api/test_clinical_router.py` (`authorName` assertions on create/list)
- [x] Frontend tests updated: `ClinicalEntriesPage.test.tsx` (10/10 passing)
- [x] OpenAPI regenerated + frontend types regenerated, both committed
- [x] Traceability matrix updated (SR-012, SR-013 → TASK-066b → tests)
- [x] TASK-092 / TASK-092a caveats referencing these two gaps removed; AC/DoD boxes confirmed met

## QA sign-off

- **Date:** 2026-06-30
- **Evidence:** 493 backend tests pass (`uv run pytest`); 119 frontend tests pass (`npx vitest run`);
  `npm run lint` and `npm run typecheck` clean; ruff + mypy clean on changed backend files.
