---
id: "TASK-235"
type: task
title: "Return exactly decoded frames as application/octet-stream, proven by real decodes"
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
  - target: "PRB-046"
    relation: relates_to
  - target: "TASK-234"
    relation: relates_to
  - target: "ADD-015"
    relation: relates_to
  - target: "SOUP-015"
    relation: relates_to
  - target: "SOUP-037"
    relation: relates_to
  - target: "TS-019"
    relation: relates_to
tags: ["cr:CR-008", "control:design", "backend"]
---

# TASK-235 — Return exactly decoded frames as application/octet-stream, proven by real decodes

- **Software items / units:** `U-DICOMBE-Studies` (`router.py`, `dicom.py`; ADD-015).
- **PRB:** PRB-046. **CR:** CR-008 (D-4 (a), D-7; decision D-A).
- **Depends on:** TASK-234 (fixtures helper, allow-list in place).
- **Size:** M (`router.py`, `dicom.py` if needed, new `tests/test_frame_decode.py`,
  `tests/test_studies_endpoint.py`, `tests/test_size_bounds.py`; records).

## Objective

- `?frame=N` for a supported syntax and 0 ≤ N < frames: 200, `Content-Type: application/octet-stream`, body
  `pixel_array[N].tobytes()` (single-frame: `pixel_array.tobytes()` for N = 0), layout as ADD-015 1.3
  "Frame response" (SR-017 AC 9). Never `application/dicom`.
- Without `frame`: 200, `application/dicom`, body byte-identical to the stored object, for any syntax (AC 8).
- N ≥ frames: the existing 400 problem (unchanged text), now shown with a real decode.
- The route's `responses=` documents the 200 of both media types and the frame layout.

## Design

- `stream_dicom` returns `(bytes, media_type)` (or the router chooses the type from `frame is None`); the
  router passes it to `Response(media_type=...)`. Smallest change wins; keep the audit and error paths as
  they are.
- `responses={200: {"description": <layout>, "content": {"application/dicom": {}, "application/octet-stream": {}}}, 400: …, 502: …}`.
- No core OpenAPI change: the module router is mounted at start-up and is not in the core export
  (`app.export_openapi` builds `create_app()` without the lifespan). Verify, do not assume (Verification).

## Steps

Test first: the media-type and real-decode tests fail on `HEAD` + TASK-234 (wrong media type).

1. `tests/test_frame_decode.py` (fixtures from TASK-234; real pydicom and NumPy, no stub):
   - `test_frame_bytes_equal_known_values` parametrised over the five syntaxes × {single-frame 8-bit
     unsigned MONOCHROME2, multi-frame (3 frames) 16-bit signed MONOCHROME2, single-frame 8-bit RGB
     (samples per pixel 3)} with distinct known values per frame: for each N, 200,
     `application/octet-stream`, body equals `expected[N].astype(expected.dtype.newbyteorder("="), copy=False).tobytes()`
     (native order; this pins the Big Endian case to native bytes). Skip combinations pydicom cannot
     write for a syntax only with a reason in the test (RLE writes need `pydicom`'s RLE encoder, which needs
     only NumPy; expected available).
   - `test_last_frame_and_out_of_range`: N = frames − 1 → 200; N = frames → 400 problem, existing text, no
     pixel bytes.
   - `test_whole_object_is_byte_identical` (uncompressed and a JPEG Baseline object): no `frame` → 200,
     `application/dicom`, `body == stored bytes`.
2. `tests/test_studies_endpoint.py`: update any assertion of `application/dicom` on a frame response to
   `application/octet-stream`; keep the auth, 403 and audit tests unchanged.
3. `tests/test_size_bounds.py`: add `test_real_decode_at_small_size_within_bounds` (a real 64 × 64 × 2-frame
   object, bounds at their defaults: 200, exact bytes) and make TC-019.3's truncated case real
   (`test_truncated_pixel_stream_real_decode`: pixel data one byte short → 400 `dicom_decode_failed`, no
   image) in addition to the stubbed case. The 1 GiB case (TC-019.4) keeps its stub.
4. Implement (Design).
5. Records (same commit): **TS-019** (1.2 from TASK-234, stays `in_review`): **TC-019.9** (step 1 exact
   values; SR-017 AC 9), **TC-019.10** (whole object; AC 8), **TC-019.11** (last frame and out of range
   with real decode; AC 9); TC-019.3 lists the real truncated test; TC-019.4 note "1 GiB case stubbed, a real
   small decode is TC-019.3/test_real_decode_at_small_size_within_bounds"; unit acceptance criteria:
   frame media type and layout; version-history line.

## Verification

- `cd backend && uv run pytest modules/dicom_viewer/tests -q`; whole backend suite;
  `uv run ruff check . && uv run black --check . && uv run mypy app`.
- `cd backend && uv run python -m app.export_openapi --output openapi/openapi.json && git diff --exit-code openapi/openapi.json`:
  no diff. If there is one, the CLAUDE.md contract workflow applies (`cd frontend && npm run generate:types`,
  commit both generated files) and the task records why.
- Mutation checks, recorded: (a) media type back to `application/dicom` → TC-019.9 fails; (b) return
  `pixel_array.tobytes()` (all frames) → TC-019.9 multi-frame fails; (c) byte-swap removed from the
  expectation → the Big Endian case shows whether pydicom returns native order (record the outcome).
- `traceability-check` on TASK-235, TS-019, CR-008: 0 errors. `graphify update .`.

## Acceptance criteria

- [ ] For every D-3 (a) syntax, single- and multi-frame, `?frame=N` returns 200 `application/octet-stream`
  with exactly frame N's known values; N ≥ frames is the 400 problem (SR-017 AC 9; TC-019.9, TC-019.11).
- [ ] Without `frame`, the stored object is returned byte-for-byte as `application/dicom` (AC 8; TC-019.10).
- [ ] One real decode at a small size and a real truncated decode pass alongside the stubbed bound tests
  (AC 6; TC-019.3); the core OpenAPI export is unchanged or regenerated per CLAUDE.md.

## Definition of Done

- [ ] Tests written first and seen failing; suites, Ruff, Black, mypy green; mutation checks recorded
- [ ] TS-019 updated; `traceability-check` 0 errors; `graphify update .` run

## Version history

- 1.0 (2026-11-25) — Created at the CR-008 Plan stage (Software Architect role). `draft`.
