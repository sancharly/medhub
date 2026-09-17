---
id: "PRB-006"
type: problem-report
title: "DICOM frame endpoint decodes pixel data with no size or decompression bound"
status: open
criticality: major
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["security", "hazard:availability"]
---

# PRB-006 — DICOM frame endpoint decodes pixel data with no size or decompression bound

## Observed

`backend/modules/dicom_viewer/.../dicom.py` calls `pydicom.dcmread(...).pixel_array` on the `?frame=` path with no limit on object size or decoded dimensions, so a crafted or simply very large study can exhaust memory.

## Impact

Denial of service against the whole API process, which serves every other clinical request. Touches SR-017 and SR-026.

## Safety evaluation

Contributes to RISK-007 (clinical information unavailable) and RISK-003 (incorrect DICOM rendering: a partially decoded object must fail loudly, not render).

## Resolution

Partly covered by TASK-135 (streaming upload/download, draft); the explicit decode bound is not. Proposed: bound object size and decoded pixel count, and reject beyond the limit with an RFC 7807 error. Needs the bound added to TASK-135 or its own task.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Medium.
