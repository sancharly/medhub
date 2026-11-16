---
id: "TS-019"
type: test-specification
title: "DICOM image opening and rendering verification"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-15"
links:
  - target: "SR-017"
    relation: verifies
tags: ["level:unit", "level:integration", "class:B", "cr:CR-006"]
---

# TS-019 — DICOM image opening and rendering verification

## Scope

Software requirement covered: SR-017 AC 6 (stored-size and declared-decoded-size bounds before any pixel
decode; a failed decode returns an error and no image), TASK-218 (PRB-006; RISK-003, RISK-007; SR-026 AC 3
as context for TC-019.4). SR-017 AC 1 to AC 5 (opening, modalities, ordering, scaling, authorization) belong
to the unfinished DICOM viewer phase and have no test case here yet. Software item under test: SI-MOD-DICOM-BE
`U-DICOMBE-Studies` (`backend/modules/dicom_viewer/dicom_viewer/dicom.py`, `router.py`, ADD-015), over
`AttachmentService.open(..., max_bytes=)` (ADD-012). Levels: unit and integration (the module router mounted
on a FastAPI app with the real `AttachmentService`, a fake object store and the RFC 7807 handlers).

## Preconditions and environment

Branch `fix/review-2026-07-reliability`. Backend Python 3.12 with the dependencies locked in
`backend/uv.lock`; pydicom 3.0.2 (SOUP-015). NumPy is not installed in any environment (SOUP-015, PRB-048),
so the pixel decode cannot succeed; `Dataset.pixel_array` is replaced by a `PropertyMock` (a stub returning
one 2-D frame, or raising). The tests therefore verify the bounds, the order of the checks and the error
path, not a real render (CR-006 finding P-6; a real render stays with PRB-048). No database, Redis or object
store is needed: the repository is a mock and the store is `FakeObjectStore` (TASK-217). Synthetic datasets
are built in the test with pydicom (explicit VR little endian, an `OB` PixelData element).

## Test cases

| ID | Verifies (SR / AC) | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-019.1 | SR-017 AC 6 | `backend/modules/dicom_viewer/tests/test_size_bounds.py::test_stored_size_over_bound_refused_before_read` | An attachment whose record says 150 MiB + 1 (157286401 bytes; `dicom_max_stored_bytes` is 157286400) is refused with a 400 `application/problem+json` response naming the limit, with `errors[0].rule` `dicom_stored_size_exceeded`; the object store receives no call and `pixel_array` is never touched | Status 400, problem media type, detail names 157286400, `store.calls == []`, `pixel_array` not called. Negative control: drop `max_bytes=` in the router and the test fails |
| TC-019.2 | SR-017 AC 6 | same file: `test_declared_decoded_size_over_bound_refused_with_small_stored_bytes`, `test_declared_decoded_size_counts_frames_samples_and_bytes`, `test_header_without_declared_size_is_refused` | A small stored object (under 1 KiB) whose header declares 32768 x 32769 x 8 bits (1 GiB + 32768), and one that exceeds the bound only through `NumberOfFrames` x 2 bytes, is refused with a 400 problem whose error rule is `dicom_decoded_size_exceeded`; a header with `Rows` = 0 is refused with rule `dicom_decode_failed` (no guess); `pixel_array` is never touched in any of them | Status 400, problem media type, `errors[0].rule` as stated, `pixel_array` not called. Negative control: remove `_check_declared_decoded_size` and the first two fail |
| TC-019.3 | SR-017 AC 6 | same file: `test_truncated_pixel_stream_gives_error_and_no_image` | When the decode raises (stubbed: the amount of pixel data is shorter than expected) the response is a 400 problem with rule `dicom_decode_failed`; the body holds no image bytes and the media type is not `application/dicom` | Status 400, problem media type, `errors[0].rule == "dicom_decode_failed"`, no frame bytes in the body |
| TC-019.4 | SR-017 AC 6; SR-026 AC 3 | same file: `test_reference_study_at_bounds_not_refused` | A 150 MiB (157286400 bytes) stored object whose header declares exactly 1 GiB (8192 x 8192 x 8 frames x 2 bytes) passes both checks: the store is read, `pixel_array` is called once (stub) and the frame is returned with status 200 | Status 200, body is the stubbed frame, `pixel_array` called once, `get_object` called. Context, not verified: the 10-second budget of SR-026 AC 3 for a real decode (NumPy absent; PRB-048) |
| TC-019.5 | SR-017 AC 6; SR-026 AC 3 | System level: upload a real DICOM study on a started stack and open a frame through the viewer route (`GET /studies/{attachment_id}?frame=0`) | A rendered frame is returned within 10 s | **Not executed (2026-11-15, TASK-226): not possible.** On the started stack `dicom_viewer` is not installed and `importlib.metadata.entry_points(group="medhub.modules")` is empty, so the router is not mounted (PRB-048); NumPy is not installed, so `pixel_array` cannot decode (PRB-046). Only pydicom 3.0.2 is present. No real render exists; TC-019.1 to TC-019.4 (stubbed decode) passed the same day (31 tests in `backend/modules/dicom_viewer/tests`) |

## Acceptance criteria (class B unit level)

Unit acceptance (§5.5.3): the stored bound is compared with the attachment record before the store is read;
the declared decoded size is computed from `Rows`, `Columns`, `NumberOfFrames` (default 1), `SamplesPerPixel`
(default 1) and `BitsAllocated` rounded up to whole bytes, read with `stop_before_pixels=True`, and a missing,
non-numeric or non-positive attribute is refused; an exact-bound object is accepted and one byte (stored) or
one unit over (decoded) is refused; any exception from the full read or `pixel_array` becomes a problem and
never partial bytes; the frame-out-of-range problems are unchanged. Both limits are settings
(`dicom_max_stored_bytes` = 157286400, `dicom_max_decoded_bytes` = 1073741824), exactly 150 MiB and 1 GiB
(CR-006 D-2).

## Verification results

See TASK-218 "Implementation record (Software Developer, 2026-11-13)".

## Version history

- 1.0 (2026-11-13): TASK-218. Created for SR-017 AC 6 (TC-019.1 to TC-019.4). `in_review`.
- 1.0 (2026-11-13): QA review of TASK-218 (round 2): `approved` (status only; content unchanged).
- 1.1 (2026-11-15) — TASK-226 (CR-006 verification): TC-019.5 added (real render on a started stack), recorded as not executable (PRB-048, PRB-046); TC-019.1 to TC-019.4 re-run green. Content change on an approved record, so the approval record is cleared: `in_review`.
- 1.1 (2026-11-15) — QA review of TASK-226 (round 2): `approved` (status only; content unchanged).
