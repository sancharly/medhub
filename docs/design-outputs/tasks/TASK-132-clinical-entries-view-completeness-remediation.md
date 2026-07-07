---
id: "TASK-132"
type: task
title: "Clinical-entries view completeness (remediation)"
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
  - target: "SR-015"
    relation: implements
  - target: "SR-016"
    relation: implements
  - target: "TASK-092"
    relation: relates_to
  - target: "TASK-123"
    relation: relates_to
  - target: "TASK-125"
    relation: relates_to
  - target: "TASK-101"
    relation: relates_to
tags: ["phase:7-frontend-core", "remediation-of:TASK-092", "original-id:TASK-092a"]
---

- **Phase:** 7 — Frontend core
- **Implements / restores:** SR-012, SR-013, SR-015/016; remediates TASK-092
- **Depends on:** TASK-092, TASK-044a (patient roster, for navigation), TASK-066a (multipart upload), TASK-101 (module gating)
- **Branch:** `feature/clinical-entries-completeness`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-092 verdict **PARTIAL** (phase-7 QA, confirmed)

*Originally filed as TASK-092a.*

## Objective

The clinical-entries view has several unmet acceptance criteria found in the phase-7 QA:
- `CreateEntryForm.tsx` captures only a **date** and hard-codes `T00:00:00Z`, discarding the **time**
  (SR-012 AC-2 requires date and time).
- `AttachmentUpload.tsx` reads `files?.[0]` only and the `<input>` has no `multiple` — **single-file
  only** despite SR-013 AC-1 ("one or more").
- `AttachmentItem.tsx` is **never mounted** — uploaded attachments are not listed in the entry view.
- When it is mounted, its "Open in viewer" link gates only on `contentType==="application/dicom"` and
  does not check `/me/modules`, so the viewer link shows even when the DICOM module is disabled
  (SR-015/016 gating).

## Implementation detail

- Add a time input (or datetime-local) to `CreateEntryForm` and send full datetime.
- Allow multiple files in `AttachmentUpload` (`multiple` + iterate), aligned with TASK-066a multipart.
- Render `AttachmentItem` for each attachment in `ClinicalEntryList`/`ClinicalEntriesPage`.
- Gate the "Open in viewer" affordance on the DICOM module being enabled (`GET /me/modules`).
- Show the authoring doctor's name (not raw `authorId`).

## Acceptance criteria

- [x] Clinical entry create captures date **and** time.
- [x] A doctor can attach **one or more** files in a single upload.
- [x] Attachments are listed under their entry; DICOM "open in viewer" appears **only** when the module is enabled.
- [x] Author is shown by name for every entry, using the `authorName` field returned by the server (TASK-066b).

## Definition of Done

- [x] Lint + type-check pass
- [x] Component tests cover multi-file, attachment listing, and module-gated viewer link (mocks match the real contract) — `ClinicalEntriesPage.test.tsx`
- [x] Verified end-to-end once TASK-044a/066a land
- [x] Traceability row updated (SR-012/SR-013 → TASK-092a → tests)

## Implementation notes (2026-06-30)

- `CreateEntryForm.tsx`: added a `type="time"` field alongside the existing date field; submit builds
  `occurredAt` via `new Date(\`${date}T${time}\`).toISOString()`.
- `AttachmentUpload.tsx`: `<input>` now has `multiple`; `handleChange` iterates `Array.from(files)` and
  uploads each via `Promise.all`.
- `AttachmentItem.tsx` is now mounted per-entry via `ClinicalEntryList.tsx`'s new `EntryAttachments`
  component, backed by `useQuery(['attachments', entryId], () => apiClient.listAttachments(entryId))`
  against the new `GET /clinical-entries/{entry_id}/attachments` endpoint (TASK-066b), so attachments
  persist across page reloads.
- `AttachmentItem.tsx` now fetches `GET /me/modules` (`apiClient.listMyModules()`) and only shows
  "Open in viewer" when `"dicom-viewer"` is present, in addition to the existing content-type check.
- Author name: the entry list renders the server-provided `entry.authorName` field directly
  (TASK-066b), resolved for every author, not just the viewer.
