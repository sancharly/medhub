---
id: "TASK-237"
type: task
title: "Remove the Open in viewer link from attachments and keep Download"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-25"
updated: "2026-11-25"
links:
  - target: "SR-017"
    relation: implements
  - target: "RISK-003"
    relation: mitigates
  - target: "CR-008"
    relation: relates_to
  - target: "PRB-048"
    relation: relates_to
  - target: "SR-015"
    relation: relates_to
  - target: "ADD-022"
    relation: relates_to
  - target: "TS-005"
    relation: relates_to
  - target: "TS-019"
    relation: relates_to
tags: ["cr:CR-008", "control:information", "frontend"]
---

# TASK-237 — Remove the Open in viewer link from attachments and keep Download

- **Software items / units:** SI-FE-CORE `AttachmentItem` (`frontend/src/core/clinical/AttachmentItem.tsx`);
  ADD-022 1.1 records that no viewer entry point exists until #29.
- **PRB:** PRB-048. **CR:** CR-008 (D-5 (a); decision D-A).
- **Depends on:** none (independent of the backend tasks; can run in parallel with TASK-233 to TASK-236).
- **Size:** S (`AttachmentItem.tsx`, `AttachmentItem.test.tsx`; records).

## Objective

No attachment shows a control labelled or linking as a viewer; every attachment keeps its Download link
(new tab, `noopener`) (SR-017 AC 11). `AttachmentItem` no longer calls `useMyModules`.

Keep `frontend/src/modules/useMyModules.ts` and its tests: the viewer phase (#29, TASK-101, TASK-102)
reuses them. The hook then has no consumer in code; that is expected and recorded in ADD-021 by TASK-238.
Do not touch any other frontend file (CR-008 boundary).

## Steps

1. `AttachmentItem.test.tsx` first: replace the viewer tests with
   - `shows the file name and a Download link to the attachment` (kept);
   - `offers no viewer for a DICOM attachment even when the DICOM module is enabled` (MSW `/me/modules`
     returns `dicom-viewer`): no element with role link or button whose name matches `/viewer/i`, and no
     link whose `href` is the module route or the core URL other than Download;
   - `offers no viewer for a non-DICOM attachment, and keeps Download`;
   - `does not request the user's module list` (MSW records no `/me/modules` request).
   The DICOM-enabled case must fail on `HEAD`.
2. `AttachmentItem.tsx`: remove the viewer link, the `useMyModules` import and the `DICOM_MODULE_KEY`
   constant (orphans of this change only).
3. Records (same commit):
   - **TS-005** (approved 1.5 → 1.6, `in_review`, remove the approval record): **TC-005.6** marked
     "Retired 2026-11-25 (CR-008 D-5): the viewer link it verified is removed; SR-015 AC 3 and AC 4 keep
     their server-side verification, TC-005.2". Keep the row (IDs are never reused); remove the
     `AttachmentItem` unit acceptance line or mark it retired. Version-history line.
   - **TS-019** (stays `in_review`): new **TC-019.12** — Verifies SR-017 AC 11; the step-1 tests.

## Verification

- `cd frontend && npm run test -- --run src/core/clinical/AttachmentItem.test.tsx`, then
  `npm run test -- --run`, `npm run lint`, `npm run typecheck`, `npm run build`, on **Node 20 or later**
  (local default is 18; CI uses 24.22.2: e.g. `npx -y node@24.22.2 …` or `nvm use 24`).
- Mutation check, recorded: put the link back → the DICOM-enabled test fails.
- `traceability-check` on TASK-237, TS-005, TS-019, CR-008: 0 errors. `graphify update .`.

## Acceptance criteria

- [ ] No attachment shows a viewer control, whatever the module list; Download stays (SR-017 AC 11; TC-019.12).
- [ ] `AttachmentItem` makes no `/me/modules` request; `useMyModules` is kept for #29; TC-005.6 retired.

## Definition of Done

- [ ] Tests written first and seen failing; frontend suite, lint, typecheck and build green on Node 20+
- [ ] TS-005 and TS-019 updated; `traceability-check` 0 errors; `graphify update .` run

## Version history

- 1.0 (2026-11-25) — Created at the CR-008 Plan stage (Software Architect role). `draft`.
