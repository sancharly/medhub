---
id: "TASK-146"
type: task
title: "Unit tests for the session provider, attachment gating and the CSRF helper"
status: draft
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-11-13"
links:
  - target: "NFR-006"
    relation: implements
  - target: "SR-030"
    relation: implements
  - target: "SR-015"
    relation: implements
  - target: "SR-031"
    relation: implements
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-017"
    relation: relates_to
  - target: "RISK-005"
    relation: relates_to
  - target: "RISK-004"
    relation: relates_to
  - target: "TS-001"
    relation: relates_to
  - target: "TS-005"
    relation: relates_to
  - target: "TS-011"
    relation: relates_to
  - target: "TASK-143"
    relation: relates_to
  - target: "TASK-144"
    relation: relates_to
  - target: "TASK-221"
    relation: relates_to
  - target: "TASK-222"
    relation: relates_to
  - target: "TASK-111"
    relation: relates_to
tags: ["phase:review-2026-07", "cr:CR-006", "verification", "frontend"]
---

# TASK-146 — Unit tests for the session provider, attachment gating and the CSRF helper

- **Software item / unit:** SI-FE-AUTH `SessionActivityProvider` (ADD-019); SI-FE-CORE `AttachmentItem`
  (ADD-020); SI-FE-APICLIENT `api/csrf.ts` (ADD-023).
- **PRB:** PRB-017 (narrowed: `AttachmentUpload.test.tsx` exists since TASK-206). **CR:** CR-006 (D-9).
- **Depends on:** TASK-143, TASK-144, TASK-221, TASK-222 (tests target their final shape).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** S (three new test files `frontend/src/auth/SessionActivityProvider.test.tsx`,
  `frontend/src/core/clinical/AttachmentItem.test.tsx`, `frontend/src/api/csrf.test.ts`; records TS-001,
  TS-005, TS-011 unit acceptance criteria). No production code change; a defect found goes to a PRB.

## Objective

IEC 62304 §5.5 (class B unit verification) and NFR-006 AC 3, AC 4 for three security-relevant units that have no
unit test. D-9: unit tests suffice at the unit level; system-level evidence stays in TS-001 and TS-005.

## Tests (write first; behavioural, no snapshots)

- `SessionActivityProvider`: warning dialog 2 min before the server-derived deadline (SR-030 AC 4, AC 8); extend
  re-derives the deadline from the response (SR-030 AC 8); expiry redirects once to `/login?timeout=1`
  (SR-030 AC 1, AC 2, AC 8); logout clears the query cache (SR-030 AC 5).
- `AttachmentItem`: viewer link present iff the DICOM module is in the user's modules (SR-015 AC 3); absent after
  disable (SR-015 AC 4, AC 5); non-DICOM attachments unaffected.
- `csrf.ts`: header set from the cookie for POST/PUT/PATCH/DELETE, not for GET (SR-031 AC 3); absent cookie
  tolerated (no header, no throw).
- Unit acceptance criteria written in TS-001, TS-005, TS-011 (same versions as the tasks that raised them);
  coverage of the three units reported in TASK-226's TR input.

## Acceptance criteria

- [ ] Each of the three units has a test file whose cases trace to the AC named above.
- [ ] Coverage report shows the three units exercised (lines and branches reported).

## Definition of Done

- [ ] `npm run lint`, `typecheck`, `test -- --run --coverage` green
- [ ] TS records hold the unit acceptance criteria; `traceability-check` no error for this record

## Version history

- 1.1 (2026-11-13) — CR-006 Plan stage (Software Architect). Narrowed to the three remaining units (D-1, D-9);
  `implements` SR-015 and SR-031 added; the cases follow the shapes of TASK-143, 144, 221 and 222.
