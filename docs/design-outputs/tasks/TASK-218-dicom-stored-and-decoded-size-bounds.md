---
id: "TASK-218"
type: task
title: "DICOM stored-size and decoded-size bounds before any pixel decode"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-13"
links:
  - target: "SR-017"
    relation: implements
  - target: "SR-026"
    relation: implements
  - target: "RISK-003"
    relation: mitigates
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-006"
    relation: relates_to
  - target: "ADD-015"
    relation: relates_to
  - target: "SOUP-015"
    relation: relates_to
  - target: "TASK-217"
    relation: relates_to
tags: ["cr:CR-006", "dicom", "control:protective"]
---

# TASK-218 — DICOM stored-size and decoded-size bounds before any pixel decode

- **Software item / unit:** SI-MOD-DICOM-BE (ADD-015): `dicom_viewer/dicom.py`, `dicom_viewer/router.py`.
- **PRB:** PRB-006. **CR:** CR-006 (D-2: 150 MiB stored, 1 GiB decoded; separate task, not TASK-135).
- **Depends on:** TASK-217 (`AttachmentService.open(..., max_bytes=)`).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** S (`backend/modules/dicom_viewer/dicom_viewer/dicom.py`, `router.py`; tests
  `backend/modules/dicom_viewer/tests/`; records TS-019 new, ADD-015, SOUP-015 relied-on text).

## Objective

SR-017 AC 6: before decoding any pixel data the module refuses an object over 150 MiB stored or whose
declared decoded size (rows × columns × frames × samples per pixel × bytes per sample) exceeds 1 GiB, with an
RFC 7807 error; a decode that fails part-way returns an error and no image. Today `stream_dicom` calls
`dcmread` and `pixel_array` on the whole object with no bound (`dicom.py:27-28`).

## Implementation detail

- Settings `dicom_max_stored_bytes` (157286400) and `dicom_max_decoded_bytes` (1073741824), read from the
  platform settings; no new environment variable unless the module already has a settings pattern.
- Router: `services.attachments.open(actor, id, max_bytes=dicom_max_stored_bytes)` (TASK-217): the stored
  bound is checked from the attachment record before any read.
- `stream_dicom(data, frame)`: when `frame` is given, first `dcmread(BytesIO(data), stop_before_pixels=True)`;
  compute the declared size from `Rows`, `Columns`, `NumberOfFrames` (default 1), `SamplesPerPixel`
  (default 1), `BitsAllocated` (rounded up to bytes); a missing or non-positive attribute is refused (no
  guess). Over the bound → a problem naming the limit (`dicom_decoded_size_exceeded`). Only then the full
  read and `pixel_array`, inside `try`: any exception → a problem (`dicom_decode_failed`), never partial
  bytes.
- The problem types are documented in the module's router `responses=` (the module router is not in the
  core OpenAPI export; confirm, and if it is, regenerate as an "ask first" contract change).
- **NumPy is not installed** in any environment (SOUP-015 review, PRB-048), so `pixel_array` always fails
  today; this task must not add NumPy (new SOUP, "ask first"). The decode path is tested with `pixel_array`
  stubbed; the real render stays with PRB-048 (finding P-6).

## Tests (write first)

- `test_stored_size_over_bound_refused_before_read` (SR-017 AC 6): attachment record of 150 MiB + 1;
  problem response; the store is not read.
- `test_declared_decoded_size_over_bound_refused_with_small_stored_bytes` (SR-017 AC 6): a small synthetic
  dataset whose header declares 1 GiB + 1; problem; `pixel_array` never called.
- `test_truncated_pixel_stream_gives_error_and_no_image` (SR-017 AC 6): stubbed decode raises; problem
  response, empty body.
- `test_reference_study_at_bounds_not_refused` (SR-017 AC 6, SR-026 AC 3): a 150 MiB stored object whose
  header declares ≤ 1 GiB passes both checks (decode stubbed).
- Recorded in a new TS-019 "DICOM image opening and rendering verification" (`verifies` SR-017), TC-019.1
  to TC-019.4. No TS verifies SR-017 today.

## Acceptance criteria

- [ ] SR-017 AC 6: both bounds checked before decode; errors are RFC 7807; no partial image.
- [ ] Bounds are exactly 150 MiB and 1 GiB (D-2).
- [ ] No new dependency.

## Definition of Done

- [ ] `uv run pytest modules/dicom_viewer/tests`, backend suite, `ruff`, `mypy` green
- [ ] TS-019 created (`draft` → `in_review` at handoff); ADD-015 consistent; SOUP-015 relied-on text names the
  header-only read on the module path
- [ ] `traceability-check` no error for this record

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect) for PRB-006 (D-2).
