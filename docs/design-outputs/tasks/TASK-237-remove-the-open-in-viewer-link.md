---
id: "TASK-237"
type: task
title: "Remove the Open in viewer link from attachments and keep Download"
status: approved
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

- [x] No attachment shows a viewer control, whatever the module list; Download stays (SR-017 AC 11; TC-019.12).
- [x] `AttachmentItem` makes no `/me/modules` request; `useMyModules` is kept for #29; TC-005.6 retired.

## Definition of Done

- [x] Tests written first and seen failing; frontend suite, lint, typecheck and build green on Node 20+
- [x] TS-005 and TS-019 updated; `traceability-check` 0 errors; `graphify update .` run

## Scope change (orchestrator, 2026-11-25)

`frontend/src/modules/useMyModules.test.tsx` was the visible consumer of `useMyModules` through the
`AttachmentItem` viewer link (eight tests). With the link removed (D-5) those tests could not stay as they were,
so the file is in scope: the eight tests now read the hook through a test-only probe component kept inside the
test file (every case kept: 60 s refresh, remount, failed refetch, slow network, `GroupModules`, add-member and
remove-member invalidation; the two "one reader" tests unchanged). Test-only: no production behaviour and no
SR-015 change. `frontend/src/core/clinical/ClinicalEntriesPage.test.tsx` also asserted the viewer link
(`viewer link appears when DICOM module is enabled`); it is changed the same way (test-only, consequence of D-5).

## Implementation record (Software Developer, 2026-11-25)

- `AttachmentItem.tsx`: viewer link, `useMyModules` import, `DICOM_TYPE` and `DICOM_MODULE_KEY` removed (all
  orphaned by this change only).
- `AttachmentItem.test.tsx`: four tests of step 1. On `HEAD` (link present) two fail: the DICOM-enabled case and
  `does not request the user's module list`.
- `useMyModules.test.tsx`: probe `ModulesProbe`; 11 tests green. Mutation checks (hook or invalidation broken by
  hand, then restored): no `refetchInterval` 4 fail; 60 s interval 4 fail; no `refetchOnMount` 1 fails; query
  function swallowing errors into `[]` 2 fail; no invalidation in `GroupModules` 1 fails; none in `GroupMembers`
  (add and remove) 2 fail.
- Node 20.19.0 (nvm): frontend suite 41 files, 412 tests passed; lint, typecheck, build clean.
- TS-005 1.6 (TC-005.5 reworded, TC-005.6 retired) and TS-019 1.2 (TC-019.12) updated; both `in_review`.

## QA review (QA Engineer, 2026-11-25, round 1)

**Verdict: APPROVED.** No CRITICAL or HIGH finding; `traceability-check` on CR-008, TASK-237, TS-005 and
TS-019 (43 records in scope, 486 indexed): 0 errors, 21 warnings (W5/W6, all from CR-008 records in flight or
pre-existing; the W5s on TS-005 clear with this approval).

- Node 20.19.0 (nvm; Node 24 not available locally): frontend suite 41 files, 412 tests passed; `npm run lint` 0;
  `npm run typecheck` 0; `npm run build` 0, initial JS 160.44 kB gzip within the 165 kB budget.
- Fails on `HEAD`: `HEAD` `AttachmentItem.tsx` against the new tests: the DICOM-enabled case, the no-request case
  and the ClinicalEntriesPage enabled case fail (3). Viewer ungated by the module: 2 fail.
- `useMyModules.test.tsx` negative controls reproduced: no `refetchInterval` 4 fail; no invalidation in
  `GroupMembers` 2 fail; none in `GroupModules` 1 fails; no `refetchOnMount` 1 fails. The 11 test names are
  unchanged and every assertion is kept; only the reader changed (`ModulesProbe`). All files restored.
- Prettier (no Prettier step in CI): the changed files pass, except `ClinicalEntriesPage.test.tsx`, whose two
  violations (lines 158 and 202) are on `HEAD` too and lie outside the task's hunks.
- Orphans: `DICOM_TYPE` and `DICOM_MODULE_KEY` were module-private; `useMyModules` has no production consumer
  (expected, ADD-021 via TASK-238); `apiClient.listMyModules`, `getAttachmentUrl` and `queryKeys.myModules`
  are still used, and nothing in `generated/types.ts` became orphaned.
- `ClinicalEntriesPage.test.tsx` change is a justified consequence of D-5: its enabled-module test asserted
  the link; the disabled-module test is renamed only.

Findings (not blocking):

- **MEDIUM** TS-019 Scope, software item and environment do not cover TC-019.12 (`TS-019` "Scope" and
  "Preconditions and environment"): they name SR-017 AC 6 and AC 10, SI-MOD-DICOM-BE and Python only. Add
  SR-017 AC 11, SI-FE-CORE `AttachmentItem` and the frontend environment (Node 24, `frontend/package-lock.json`,
  Vitest with MSW), and name the two `ClinicalEntriesPage.test.tsx` tests in TC-019.12, before TS-019 is
  approved.
- **LOW** TS-005 Notes still say the propagation "to other users' UI is verified by TC-005.5"; since 1.6 it is
  verified at the hook. Reword it at the next TS-005 change.
- **LOW** `useMyModules.test.tsx`: four statements (`server.use(...)` in the three admin tests and
  `installedModules`) were reformatted by Prettier even though their content did not change (surgical-change
  rule). Harmless; nothing to do now.

## Version history

- 1.0 (2026-11-25) — Created at the CR-008 Plan stage (Software Architect role). `draft`.
- 1.0 (2026-11-25) — Scope extended to `useMyModules.test.tsx` and `ClinicalEntriesPage.test.tsx` (test-only). Implemented; `draft → in_review` for QA.
- 1.0 (2026-11-25) — QA review of TASK-237 (round 1): `in_review → approved` (status only; content unchanged).
