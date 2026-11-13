---
id: "PRB-017"
type: problem-report
title: "Security-relevant frontend units have no unit tests"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-13"
criticality: major
links: []
tags: ["verification", "regulatory"]
---

# PRB-017 — Security-relevant frontend units have no unit tests

## Observed

`SessionActivityProvider`, `AttachmentItem` (module-gated DICOM link), `AttachmentUpload` with `client.uploadAttachment`, and `api/csrf.ts` have no unit tests; only `useIdleTimer` is covered.

## Impact

IEC 62304 §5.5 requires unit verification for class B software. These units implement SR-030, SR-015 and SR-031 behaviour and are currently verified by manual testing only.

## Safety evaluation

Contributes to RISK-005, RISK-004 and RISK-001 indirectly: an unverified control is not a control (PLAN-005).

## Investigation

Narrowed on 2026-11-13 (CR-006 D-1, D-9). `core/clinical/AttachmentUpload.test.tsx` now exists (added with TASK-206), so the upload unit has a test. **Remaining gap:** no test file exists for `auth/SessionActivityProvider.tsx` (SR-030 AC 1 to AC 4) or `core/clinical/AttachmentItem.tsx` (SR-015 AC 3, AC 4), and `api/csrf.ts` (SR-031 AC 3) has no dedicated test (`api/client.test.ts` only uses the CSRF cookie as a fixture). Unit tests are sufficient at the unit level (D-9); the system-level evidence stays in TS-001 and TS-005.

## Resolution

TASK-146 (draft) under CR-006 — unit tests for `SessionActivityProvider`, `AttachmentItem` and `api/csrf.ts`, with the TS record that verifies the SRs. **Stays `open`.**

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding T′.

## Version history

- 1.0 (2026-09-17) — Created from the July 2026 code review. `open`.
- 1.1 (2026-11-13) — CR-006: Investigation added; scope narrowed to the three units still without tests (D-9). Stays `open`.
