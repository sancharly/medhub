---
id: "PRB-017"
type: problem-report
title: "Security-relevant frontend units have no unit tests"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
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

Contributes to RISK-005, RISK-004 and RISK-001 indirectly: an unverified control is not a control (ADD-003).

## Resolution

TASK-146 (draft) — unit tests for each of those units, with the TS record that verifies the SRs.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding T′.
