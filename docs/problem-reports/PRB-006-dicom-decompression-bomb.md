---
id: "PRB-006"
type: problem-report
title: "DICOM frame endpoint decodes pixel data with no size or decompression bound"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-13"
criticality: major
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

TASK-218 (in review, 2026-11-13), CR-006 D-2 and D-20, SR-017 AC 6. Two settings, `dicom_max_stored_bytes`
(157286400, 150 MiB) and `dicom_max_decoded_bytes` (1073741824, 1 GiB), also in `infra/.env.example`.
The module router opens the attachment with `AttachmentService.open(..., max_bytes=)`, which refuses
an attachment whose record is larger with a 400 `validation-error` problem before the object store is
read. `stream_dicom`, on the `?frame=` path, first reads the header with `stop_before_pixels=True` and
computes rows x columns x frames x samples per pixel x bytes per sample (`BitsAllocated` rounded up);
a missing or non-positive attribute is refused (`dicom_decode_failed`), a size over 1 GiB is refused
(`dicom_decoded_size_exceeded`), both as the existing 400 `validation-error` problem with the rule in
`errors[]`. Only then are the full read and `pixel_array` run, inside a `try`: any exception gives a
`dicom_decode_failed` problem and never partial bytes. The route documents the 400 problem in
`responses=`; the module router is not in the core OpenAPI export (export byte-identical, no contract
change). Verified in the working tree: TC-019.1 to TC-019.4 in TS-019 1.0 (6 tests in
`backend/modules/dicom_viewer/tests/test_size_bounds.py`; removing the router `max_bytes=` or the header
check fails the matching tests); backend suite, ruff, mypy. Not verified: a real render, because NumPy is
not installed and `pixel_array` cannot succeed in any environment (SOUP-015; PRB-048, CR-006 finding P-6),
so the decode is stubbed in the tests. QA approved TASK-218 (2026-11-13): `resolved` (CR-006 `resolves` PRB-006); `closed` when CR-006 closes.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Medium.

## Version history

- 1.1 (2026-11-13) — TASK-218: `## Resolution` written, implemented and verified in the working tree (decode stubbed, NumPy absent). `open → investigating`; `resolved` when QA approves TASK-218.
- 1.2 (2026-11-13) — QA review of TASK-218 (round 2): approved; `investigating → resolved`.
