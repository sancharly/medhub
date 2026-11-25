---
id: "TASK-235"
type: task
title: "Return exactly decoded frames as application/octet-stream, proven by real decodes"
status: approved
version: "1.2"
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

- [x] For every D-3 (a) syntax, single- and multi-frame, `?frame=N` returns 200 `application/octet-stream`
  with exactly frame N's known values; N ≥ frames is the 400 problem (SR-017 AC 9; TC-019.9, TC-019.11).
- [x] Without `frame`, the stored object is returned byte-for-byte as `application/dicom` (AC 8; TC-019.10).
- [x] One real decode at a small size and a real truncated decode pass alongside the stubbed bound tests
  (AC 6; TC-019.3); the core OpenAPI export is unchanged or regenerated per CLAUDE.md.

## Definition of Done

- [x] Tests written first and seen failing; suites, Ruff, Black, mypy green; mutation checks recorded
- [x] TS-019 updated; `traceability-check` 0 errors; `graphify update .` run

## Version history

- 1.0 (2026-11-25) — Created at the CR-008 Plan stage (Software Architect role). `draft`.
- 1.1 (2026-11-25) — Implementation handed to QA (Software Developer). `in_review`.
- 1.1 (2026-11-25, QA) — Round 1 CHANGES REQUESTED (R1-1 and R1-2 HIGH, R1-3 MEDIUM, R1-4 to R1-6 LOW). Status `draft`.
- 1.2 (2026-11-25) — QA round 1 findings R1-1 to R1-5 addressed (Software Developer). `in_review`.
- 1.2 (2026-11-25, QA) — Round 2 APPROVED; R1-1 to R1-4 fixed, R1-5 corrected in PRB-095 (fix pending the human's scope decision), R1-6 no change needed. Status `approved`.

## Implementation record (Software Developer, 2026-11-25)

- **Code:** `router.py` returns `application/octet-stream` when `frame` is given and `application/dicom` otherwise, and `responses=` documents the 200 of both media types and the layout. `dicom.py`: `_native_bytes` writes a frame with `tobytes()` in native byte order; the frame count now comes from `NumberOfFrames` instead of `pixel_array.ndim`.
- **Two defects found by the real decodes, both in this task's unit and fixed here:** (1) pydicom returns the array of an Explicit VR Big Endian object with a big-endian dtype, so `tobytes()` alone would serve big-endian samples, against ADD-015; (2) a single-frame RGB array is 3-D, and the old `ndim == 2` test treated it as a multi-frame object of `rows` frames.
- **Tests, written first.** On HEAD, with the new tests added, 16 of them failed (media type, and the big-endian bytes); one more failure was the PRB-095 flake. `tests/test_frame_decode.py` (new: 15 combinations, signed read-back, last frame and out of range x2, whole object x2); `tests/test_size_bounds.py` (`test_real_decode_at_small_size_within_bounds`, `test_truncated_pixel_stream_real_decode`; the `_Frame` stub gained `dtype`, `astype` and `__getitem__` because the code now normalises the byte order and indexes by the declared frame count); `tests/fixtures.py` (`build_rle`, `build_short_pixel_data`; signed fixtures now carry negative samples). `test_studies_endpoint.py` needed no change: no test asserts `application/dicom` on a frame response.
- **Verification:** module suite 74 passed (three runs); `tests/modules` 119 passed; whole backend suite 1775 passed, 10 skipped; Ruff and Black clean; `mypy app` clean; `mypy modules/dicom_viewer/dicom_viewer` reported one `no-any-return` error at the time and this line was wrong to say "mypy clean" (QA R1-3; corrected in round 2); OpenAPI export: no diff in `backend/openapi/openapi.json`; `graphify update .` run.
- **Mutation checks:** (a) frame media type back to `application/dicom`: 16 failed; (b) all frames returned (`pixel_array`): 8 failed; (c) byte swap removed: 2 failed (Explicit VR Big Endian 16-bit signed, read-back test), so pydicom does return a non-native order for that syntax; (d) frame count from `ndim`: 5 failed (single-frame RGB). Each reverted; files identical to the tested state.
- **PRB-095** opened for a flake in the TASK-218 test `test_reference_study_at_bounds_not_refused` (random UID length); not fixed here.

## QA review — round 1 (2026-11-25): CHANGES REQUESTED

Re-run by QA on the working tree of `bug/dicom-module-install` (HEAD d576494 + this task's changes): module suite
(`--import-mode=importlib`) 74 passed; `tests/modules` 119 passed; whole backend suite with coverage 1775 passed,
10 skipped, 95.24 %; `ruff check .` 0; `ruff format --check modules/dicom_viewer` 0; `black --check .` 0; `mypy app` 0;
`mypy modules/dicom_viewer/dicom_viewer` **1 error** (R1-3); OpenAPI export: no diff. Mutations reproduced on a
scratch copy: byte swap removed, 2 failed (Big Endian 16-bit signed, read-back); frame count from `ndim`, 5 failed
(single-frame RGB). Both developer defects are fixed and pinned. Verified by QA probes, all correct: Planar
Configuration 1 RGB is returned interleaved; BitsAllocated 1 is unpacked to one byte per sample (frames not
byte-aligned too); 32-bit signed and unsigned, Little and Big Endian; 12 bits stored in 16, signed, sign-extended;
`frame=-1`, `1.5`, `abc`, empty, `1e3` give a 400 `application/problem+json`, never a 5xx; the whole object is
byte-identical as `application/dicom`. The `_Frame` stub changes do not weaken TC-019.4: every bound check runs
before `pixel_array`, and the test still asserts 200, the stubbed body and one `pixel_array` call.
`traceability-check` (CR-008 tag, CR-008, TASK-235, TS-019, PRB-095; 39 records): 0 errors.

- **R1-1 HIGH — YBR colour frames are converted to RGB, against the documented layout** — `dicom.py:144`,
  `router.py:83-86`. `ds.pixel_array` uses pydicom 3's default `as_rgb=True`: a YBR_FULL object (native or RLE
  Lossless, a supported syntax; YBR_FULL is a usual RLE colour interpretation) whose samples are (100, 50, 200)
  is served as (201, 75, 0), and YBR_FULL_422 (2 bytes per pixel stored) is served as 3 RGB samples per pixel.
  The route says "No rescale, windowing or photometric conversion is applied ... Read ... Photometric
  Interpretation from the whole object", so a client reading `YBR_FULL` converts again: wrong colours, the
  RISK-003 hazard. ADD-015 ("beyond what `pixel_array` does by default") does not say what that is. No test has a
  YBR object. → Choose and record one: (a) `ds.pixel_array_options(as_rgb=False)` before reading `pixel_array`, so
  the samples are as stored (state what happens to YBR_FULL_422); or (b) keep the conversion and state in
  `responses=` and ADD-015 (Software Architect) that YBR_FULL and YBR_FULL_422 frames are returned as RGB. Add
  TC-019.9 cases with known values for YBR_FULL native and RLE, and YBR_FULL_422 native.
- **R1-2 HIGH — the header frame count and the decoded array disagree; frame 0 can carry every frame** —
  `dicom.py:151-153`. pydicom 3.0.2 raises the frame count when the pixel data holds more frames than (0028,0008)
  declares (it only warns). With NumberOfFrames absent or 1 and data for 3 frames of 2 x 2, `pixel_array` is
  (3, 2, 2): `frame=0` returns 12 bytes (all three frames) as one frame, three times rows x columns x samples x
  bytes, and `frame=1` is refused with "1 frame". HEAD (`ndim`) returned frame 0 alone. → Take the frame shape
  from the header, `(Rows, Columns)` or `(Rows, Columns, SamplesPerPixel)`: single frame when
  `pixel_array.shape` equals it; multi-frame when `shape[1:]` equals it and `shape[0]` equals the declared
  frames; anything else is the `dicom_decode_failed` problem (an inconsistent object has no single right frame).
  Optionally assert `len(frame_data) == rows * columns * samples * itemsize`. Tests: NumberOfFrames absent and 1
  with excess data, NumberOfFrames 2 with data for 3.
- **R1-3 MEDIUM — new mypy error in the module package; the record says "mypy clean"** — `dicom.py:121`
  (`no-any-return`). `mypy modules/dicom_viewer/dicom_viewer` was 0 at TASK-234 and is 0 on HEAD. → Type the
  parameter as `numpy.ndarray` (drop `Any`) or wrap the result in `bytes(...)`; correct the Verification line of
  the implementation record.
- **R1-4 LOW — `stream_dicom` accepts a negative frame** — `dicom.py:152`. `frame=-1` returns the single frame
  (HEAD refused it with `frame != 0`) and the last frame of a multi-frame object. Not reachable over HTTP
  (`Query(ge=0)` gives the 400 problem). → `if frame < 0 or frame >= num_frames:`.
- **R1-5 LOW — PRB-095 overstates the failure rate** — `PRB-095` title and Investigation. pydicom pads a UI value
  to even length, so 63-character UIDs encode like 64; the encoded lengths are 412 bytes in 99 % and 410 in 1 %.
  QA: 68 mismatches in 3000 `_padded_to` builds (2.3 %, about one run in 45), not one in ten. Root cause and
  candidate fix confirmed; the code (TASK-218, f56216c) predates this branch. → Correct the title and the
  figures.
- **R1-6 LOW — the layout is only in documentation** — no header carries rows, columns or dtype. This meets
  D-4 (a) and AC 9 as approved (layout in `responses=` and ADD-015; the consumer reads the whole object), so no
  change is required for this task; note that the module router is not in the core OpenAPI export, so the
  `responses=` text is seen only on a running app with the module mounted.

Observation, not blocking: CR-008 D-4 (a) says "in the object's declared order"; ADD-015 and the code say
"interleaved whatever the Planar Configuration". The code matches ADD-015 (QA probe, Planar Configuration 1).

## Implementation record, round 2 (Software Developer, 2026-11-25)

- **R1-1, orchestrator decision under CR-008 D-4: samples are served as stored, with no photometric conversion.** `dicom.py` calls `ds.pixel_array_options(as_rgb=False)` before reading `pixel_array`, so pydicom's default YCbCr to RGB conversion is not applied. This matches the route's approved text ("no ... photometric conversion"). What pydicom does with `as_rgb=False` (3.0.2, probed): YBR_FULL, native and RLE Lossless, is returned as stored, (Y, Cb, Cr) interleaved, 3 samples per pixel; **YBR_FULL_422 is still upsampled by pydicom to 3 samples per pixel**, shape (rows, columns, 3), interleaved (Y, Cb, Cr), with the Cb and Cr of each horizontal pixel pair repeated for both pixels and no colour conversion (stored `Y1 Y2 Cb Cr` becomes `(Y1, Cb, Cr), (Y2, Cb, Cr)`). The route's `responses=` states exactly this. **Carry-forward to TASK-238 (Software Architect): ADD-015 "Frame response" still says "no ... photometric conversion is applied beyond what `pixel_array` does by default"; it must be reworded to the decision above (YCbCr served as stored; YBR_FULL_422 upsampled to 3 samples per pixel). ADD-015 is not edited here.** Tests: `test_ycbcr_samples_are_served_as_stored` (YBR_FULL native, YBR_FULL RLE, YBR_FULL_422; values chosen so a conversion changes them; on `as_rgb` default they differ from the expected bytes).
- **R1-2:** the frame shape is taken from the header, (Rows, Columns) or (Rows, Columns, SamplesPerPixel). The array is accepted when its shape equals that and NumberOfFrames (absent = 1) is 1, or when `shape[1:]` equals it and `shape[0]` equals NumberOfFrames; otherwise (or when the array's byte count is not NumberOfFrames x rows x columns x samples x itemsize) the response is the `dicom_decode_failed` problem "The DICOM pixel data does not match the size in the header." Out-of-range N is checked after that. Tests: `test_frame_count_disagreeing_with_the_data_is_refused` for NumberOfFrames absent with 3 frames of data, 1 with 3, 2 with 3. Residual, not refused: an object with NumberOfFrames absent and 1.5 frames of data decodes (pydicom returns one frame and a warning) and returns that frame; the header shape matches.
- **R1-3:** `_native_bytes` assigns the result to a `bytes` variable; `mypy modules/dicom_viewer/dicom_viewer` is clean (4 files). Both mypy commands are run from now on.
- **R1-4:** `stream_dicom` refuses `frame < 0` with a `ValidationProblem` before decoding; test `test_negative_frame_is_refused_before_decoding`.
- **R1-5:** PRB-095 title and figures corrected (about one run in 45); not fixed.
- **Stub:** the `_Frame` stub in `test_size_bounds.py` now takes the shape and item size of the array the header describes (8 x 8192 x 8192, 2 bytes for TC-019.4), since the shape check compares them; the bound checks and the single `pixel_array` call are asserted as before. `fixtures.py` gained `build_ybr`, `build_frame_count_mismatch` (additions only; `tests/attachments/test_dicom_validation.py` unchanged and green in the full suite).
- **Verification (working tree):** module suite 81 passed, three runs; `tests/modules` 119 passed; whole backend suite with coverage (`--cov=app --cov-fail-under=85`) 1775 passed, 10 skipped, 95.24 % (the module's new tests are in the module suite, which the root run does not collect); `ruff check .`, `black --check .`, `mypy app` and `mypy modules/dicom_viewer/dicom_viewer` all 0 errors; OpenAPI export: no diff. QA probes `probe.py` and `probe2.py` re-run: Planar Configuration 1, bits allocated 1, 32-bit, 12-in-16 unchanged; YBR_FULL native and RLE (100, 50, 200) served as (100, 50, 200); YBR_FULL_422 upsampled, unconverted; frame-count mismatches and `frame=-1` are 400 problems.
- **Mutations, round 2:** (e) `as_rgb=False` removed: 3 failed (the three YBR cases); (f) shape check removed: 3 failed (the three frame-count cases); (g) negative-frame check removed: 1 failed. Each reverted; module suite back to 81 passed.

## QA review — round 2 (2026-11-25): APPROVED

Re-run by QA on the working tree of `bug/dicom-module-install` (HEAD 7d7d0e3 + this task's changes): module suite
(`--import-mode=importlib`) 81 passed, three runs; `tests/modules` 119 passed; whole backend suite with coverage
1775 passed, 10 skipped, 95.24 %; `ruff check .` 0; `ruff format --check modules/dicom_viewer` 0; `black --check .` 0
(297 files); `mypy app` 0 (138 files); `mypy modules/dicom_viewer/dicom_viewer` 0 (4 files); OpenAPI export: no diff.
`traceability-check` (CR-008 tag, CR-008, TASK-235, TS-019, PRB-095; 39 records): 0 errors (W5/W6 only).

- **R1-1 fixed.** QA probe: YBR_FULL native and RLE stored (100, 50, 200) are served as (100, 50, 200); YBR_FULL_422 is
  upsampled to 3 interleaved samples per pixel with the pair's chroma repeated, as the route's `responses=` now says.
  Mutation: `as_rgb=False` removed, the 3 YBR cases fail. The decision (samples as stored) is within the approved
  D-4 (a) text. ADD-015 "Frame response" still says "beyond what `pixel_array` does by default"; the rewording is
  carried to TASK-238 step 5 (see the note below).
- **R1-2 fixed.** QA probe: NumberOfFrames absent or 1 with data for 3 frames, 2 with data for 3, and RGB with excess
  data are all the `dicom_decode_failed` problem for every N; consistent objects are served as before. Mutation: shape
  check removed (frame count from the header only), the 3 frame-count cases fail.
- **R1-3 fixed** (both mypy runs 0). **R1-4 fixed** (`stream_dicom(data, -1)` is a 400 problem before decoding).
- **R1-5:** PRB-095 figures corrected (about one run in 45); the fix awaits the human's CR-008 scope decision.
- **`_Frame` stub.** It now carries the header's shape and item size ((8, 8192, 8192), 2 bytes, for TC-019.4), so the
  new shape check passes for the right reason; every bound check still runs before `pixel_array`. QA mutation: the
  declared-size check removed, TC-019.2 (three tests) and TC-019.8 fail, so the stub does not mask the bounds.
- **Residual accepted (1.5 frames of data, NumberOfFrames absent).** pydicom decodes one frame and warns; the served
  bytes are exactly the frame the header describes (rows x columns x samples x bytes), and the trailing bytes, less
  than one frame, are ignored as padding would be. No other frame exists to be shown in its place, so this does not
  give a wrong image (RISK-003). Refusing it would also refuse padded objects. Record it with the ADD-015 rewording
  in TASK-238.
- Re-checked from round 1, unchanged: Planar Configuration 1 interleaved, BitsAllocated 1, 32-bit signed and unsigned
  LE/BE, 12 bits stored in 16 signed; `frame=-1`, `1.5`, `abc`, empty and `1e3` are 400 problems over HTTP; the whole
  object is byte-identical as `application/dicom`.

Note for TASK-238 (Software Architect), not blocking this task: ADD-015 "Frame response" to say YCbCr samples are
served as stored (no RGB conversion), YBR_FULL_422 upsampled to 3 samples per pixel with the pair's chroma repeated,
an array that does not match the header's frame shape and NumberOfFrames is `dicom_decode_failed`, and trailing data
under one frame is ignored. TASK-238 step 5 covers it only generically ("correct anything the implementation changed").
