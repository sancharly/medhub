# TASK-092a — Clinical-entries view completeness (remediation)

- **Phase:** 7 — Frontend core
- **Implements / restores:** SR-012, SR-013, SR-015/016; remediates TASK-092
- **Depends on:** TASK-092, TASK-044a (patient roster, for navigation), TASK-066a (multipart upload), TASK-101 (module gating)
- **Branch:** `feature/clinical-entries-completeness`
- **Status:** Not started
- **Source:** `AUDIT-LEDGER.md` — TASK-092 verdict **PARTIAL** (phase-7 QA, confirmed)

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

- [ ] Clinical entry create captures date **and** time.
- [ ] A doctor can attach **one or more** files in a single upload.
- [ ] Attachments are listed under their entry; DICOM "open in viewer" appears **only** when the module is enabled.
- [ ] Author is shown by name.

## Definition of Done

- [ ] Lint + type-check pass
- [ ] Component tests cover multi-file, attachment listing, and module-gated viewer link (mocks match the real contract)
- [ ] Verified end-to-end once TASK-044a/066a land
- [ ] Traceability row updated (SR-012/SR-013 → TASK-092a → tests)
