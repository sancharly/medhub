---
id: "TS-019"
type: test-specification
title: "DICOM image opening and rendering verification"
status: approved
version: "1.4"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-25"
links:
  - target: "SR-017"
    relation: verifies
tags: ["level:unit", "level:integration", "class:B", "cr:CR-006", "cr:CR-008"]
---

# TS-019 — DICOM image opening and rendering verification

## Scope

Software requirement covered: SR-017 AC 6 (stored-size and declared-decoded-size bounds before any pixel
decode; a failed decode returns an error and no image) and AC 10 (transfer syntax allow-list and bounded
inflation of Deflated objects before any decode; TASK-234, CR-008, PRB-046; RISK-003, RISK-007) and AC 11 (no
viewer control in the attachment list; TASK-237, CR-008 D-5, PRB-048), TASK-218 (PRB-006; RISK-003, RISK-007; SR-026 AC 3
as context for TC-019.4). SR-017 AC 1 to AC 5 (opening, modalities, ordering, scaling, authorization) belong
to the unfinished DICOM viewer phase and have no test case here yet. Software item under test: SI-MOD-DICOM-BE
`U-DICOMBE-Studies` (`backend/modules/dicom_viewer/dicom_viewer/dicom.py`, `router.py`, ADD-015) and the host helper
`backend/app/modules/dicom_support.py` (SI-MODHOST, ADD-014), SI-FE-CORE `AttachmentItem`
(`frontend/src/core/clinical/AttachmentItem.tsx`; AC 11), over
`AttachmentService.open(..., max_bytes=)` (ADD-012). Levels: unit and integration (the module router mounted
on a FastAPI app with the real `AttachmentService`, a fake object store and the RFC 7807 handlers).

## Preconditions and environment

Branch `bug/dicom-module-install` (CR-008). Backend: Python 3.12 with the dependencies locked in
`backend/uv.lock`; pydicom 3.0.2 (SOUP-015) and NumPy 2.5.5 (SOUP-037) are installed (TASK-233), and the module is
an installed workspace package (run with `--import-mode=importlib`; after a module change `uv sync --frozen`
may be needed). TC-019.1 to TC-019.4 (TASK-218, CR-006) were written when NumPy was absent and still replace
`Dataset.pixel_array` with a `PropertyMock` (a stub returning one 2-D frame, or raising): they verify the bounds,
the order and the error path, not a real render. TC-019.6 to TC-019.8 (TASK-234) use real objects built in memory
with pydicom and NumPy (`backend/modules/dicom_viewer/tests/fixtures.py`: fixed SOP Instance UID so that
the encoded length is reproducible; Implicit, Explicit LE and BE and Deflated objects, compressed-syntax
objects with arbitrary pixel bytes, deflate bombs, corrupt streams) and spy on `pydicom.dcmread` and
`Dataset.pixel_array`; the host helper is also tested on streams (`backend/tests/modules/test_dicom_support.py`).
Tests that could hang (a Deflated object over one chunk) run in a thread with a join timeout, so a
regression fails instead of stalling the suite. No database, Redis or object store is needed: the repository is
a mock and the store is `FakeObjectStore` (TASK-217). The frontend case (TC-019.12) runs on Node 24 with the
dependencies locked in `frontend/package-lock.json`, under Vitest with MSW (`npm test`).

## Test cases

| ID | Verifies (SR / AC) | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-019.1 | SR-017 AC 6 | `backend/modules/dicom_viewer/tests/test_size_bounds.py::test_stored_size_over_bound_refused_before_read` | An attachment whose record says 150 MiB + 1 (157286401 bytes; `dicom_max_stored_bytes` is 157286400) is refused with a 400 `application/problem+json` response naming the limit, with `errors[0].rule` `dicom_stored_size_exceeded`; the object store receives no call and `pixel_array` is never touched | Status 400, problem media type, detail names 157286400, `store.calls == []`, `pixel_array` not called. Negative control: drop `max_bytes=` in the router and the test fails |
| TC-019.2 | SR-017 AC 6 | same file: `test_declared_decoded_size_over_bound_refused_with_small_stored_bytes`, `test_declared_decoded_size_counts_frames_samples_and_bytes`, `test_header_without_declared_size_is_refused` | A small stored object (under 1 KiB) whose header declares 32768 x 32769 x 8 bits (1 GiB + 32768), and one that exceeds the bound only through `NumberOfFrames` x 2 bytes, is refused with a 400 problem whose error rule is `dicom_decoded_size_exceeded`; a header with `Rows` = 0 is refused with rule `dicom_decode_failed` (no guess); `pixel_array` is never touched in any of them | Status 400, problem media type, `errors[0].rule` as stated, `pixel_array` not called. Negative control: remove `_check_declared_decoded_size` and the first two fail |
| TC-019.3 | SR-017 AC 6 | same file: `test_truncated_pixel_stream_gives_error_and_no_image` | When the decode raises (stubbed: the amount of pixel data is shorter than expected) the response is a 400 problem with rule `dicom_decode_failed`; the body holds no image bytes and the media type is not `application/dicom` | Status 400, problem media type, `errors[0].rule == "dicom_decode_failed"`, no frame bytes in the body |
| TC-019.4 | SR-017 AC 6; SR-026 AC 3 | same file: `test_reference_study_at_bounds_not_refused` | A 150 MiB (157286400 bytes) stored object whose header declares exactly 1 GiB (8192 x 8192 x 8 frames x 2 bytes) passes both checks: the store is read, `pixel_array` is called once (stub) and the frame is returned with status 200 | Status 200, body is the stubbed frame, `pixel_array` called once, `get_object` called. Context, not verified: the 10-second budget of SR-026 AC 3 for a real decode (NumPy absent; PRB-048) |
| TC-019.5 | SR-017 AC 6; SR-026 AC 3 | System level: upload a real DICOM study on a started stack and open a frame through the viewer route (`GET /studies/{attachment_id}?frame=0`) | A rendered frame is returned within 10 s | **Not executed (2026-11-15, TASK-226): not possible.** On the started stack `dicom_viewer` is not installed and `importlib.metadata.entry_points(group="medhub.modules")` is empty, so the router is not mounted (PRB-048); NumPy is not installed, so `pixel_array` cannot decode (PRB-046). Only pydicom 3.0.2 is present. No real render exists; TC-019.1 to TC-019.4 (stubbed decode) passed the same day (31 tests in `backend/modules/dicom_viewer/tests`) |
| TC-019.6 | SR-017 AC 10 | `backend/modules/dicom_viewer/tests/test_transfer_syntax.py::test_unsupported_transfer_syntax_refused_before_decode` (JPEG Baseline, JPEG 2000, HTJ2K, private UID), `::test_missing_transfer_syntax_refused`, `::test_supported_syntaxes_pass_the_check` (five UIDs), `::test_invalid_transfer_syntax_uid_is_not_echoed`, `::test_file_meta_read_does_not_parse_the_data_set` (pin); host: `backend/tests/modules/test_dicom_support.py` (transfer-syntax tests) | With `frame=N`, an object whose transfer syntax, read from the file meta information only, is outside the five of CR-008 D-3 (a) (Implicit and Explicit VR Little Endian, Deflated Explicit VR Little Endian, Explicit VR Big Endian, RLE Lossless), or that declares none (no (0002,0010), no preamble, or a (0002,0010) pydicom cannot convert: an unknown VR such as `ZZ`, a `UV` of the wrong length), is refused with a 400 problem, rule `dicom_transfer_syntax_unsupported`, the message naming the UID (only when it is a valid UID of at most 64 characters of digits and dots; otherwise "invalid") or saying the object declares no transfer syntax; never a 5xx; no pixel bytes | Status 400, problem media type, rule and message as stated, not `application/dicom`, `pydicom.dcmread` and `pixel_array` never called. The pin test fails if pydicom's private `_read_file_meta_info` is missing, parses beyond group 0002 or inflates the data set (SOUP-015 1.3). Negative control: allow-list replaced by "accept all" and the refusal tests fail; syntax read after a full `dcmread` and the pin test fails |
| TC-019.7 | SR-017 AC 6 | `test_transfer_syntax.py::test_deflate_bomb_refused_without_full_inflation`, `::test_corrupt_deflate_stream_is_decode_failed`, `::test_valid_deflated_object_over_one_chunk_returns_its_frame` (with and without the pad byte); host: `test_dicom_support.py` (bomb within bound plus one chunk with every read at most one chunk, exact bound, valid objects over one chunk with and without the pad byte, corrupt, truncated and unreadable-meta streams) | A Deflated object inflating above `dicom_max_decoded_bytes` is refused with rule `dicom_decoded_size_exceeded` without inflating in full (the counted output stops at most one 64 KiB chunk above the bound); a corrupt deflate stream is refused with rule `dicom_decode_failed`; no image either way; a valid Deflated object inflating over one 64 KiB chunk, with or without the pad byte that follows an odd-length deflate stream, is accepted and its frame returned (the check ends when the deflate stream ends; QA round 1, R1-1) | Status 400, problem media type, rule as stated, counted output at most bound + 64 KiB and each read at most 64 KiB, `dcmread` and `pixel_array` never called (bound set to 1 MiB in the test); the valid-object tests return within 10 s. Negative controls: remove the Deflated bound and the bomb tests fail; stop the loop only on an empty output and the pad-byte tests fail by timeout; read the whole input at once and the bomb test fails |
| TC-019.8 | SR-017 AC 6, AC 10 | `backend/modules/dicom_viewer/tests/test_size_bounds.py::test_check_order_stored_then_syntax_then_declared_then_decode` | The order is stored size, transfer syntax, (inflated size), declared decoded size, decode: over the stored bound and unsupported gives `dicom_stored_size_exceeded` (store not read); unsupported and over the declared bound gives `dicom_transfer_syntax_unsupported`; supported and over the declared bound gives `dicom_decoded_size_exceeded` | Rules as stated, `pixel_array` never called. TC-019.1 to TC-019.4 unchanged and green. Negative control: declared size checked before the syntax and the test fails |
| TC-019.12 | SR-017 AC 11 | `frontend/src/core/clinical/AttachmentItem.test.tsx`: `shows the file name and a Download link to the attachment`, `offers no viewer for a DICOM attachment even when the DICOM module is enabled`, `offers no viewer for a non-DICOM attachment, and keeps Download`, `does not request the user's module list`; `frontend/src/core/clinical/ClinicalEntriesPage.test.tsx`: `SR-013 AC-3 / SR-017 AC 11: DICOM attachment offers no viewer link when the module is disabled`, `SR-013 AC-3 / SR-017 AC 11: DICOM attachment offers no viewer link even when the module is enabled` (TASK-237, CR-008 D-5, RISK-003) | No attachment shows a control named or linking as a viewer, whatever the module list (module enabled, disabled, non-DICOM type); every attachment keeps its Download link (new tab, `noopener`); `AttachmentItem` makes no `/me/modules` request | All listed tests pass; on the previous implementation (viewer link present) the DICOM-enabled case and the no-request case fail |

## Acceptance criteria (class B unit level)

Unit acceptance (§5.5.3): the stored bound is compared with the attachment record before the store is read;
the declared decoded size is computed from `Rows`, `Columns`, `NumberOfFrames` (default 1), `SamplesPerPixel`
(default 1) and `BitsAllocated` rounded up to whole bytes, read with `stop_before_pixels=True`, and a missing,
non-numeric or non-positive attribute is refused; an exact-bound object is accepted and one byte (stored) or
one unit over (decoded) is refused; any exception from the full read or `pixel_array` becomes a problem and
never partial bytes; the frame-out-of-range problems are unchanged. Both limits are settings
(`dicom_max_stored_bytes` = 157286400, `dicom_max_decoded_bytes` = 1073741824), exactly 150 MiB and 1 GiB
(CR-006 D-2).

From 1.3 (TASK-234): the transfer syntax is read from the file meta information only (group 0002, always
Explicit VR Little Endian) by the host helper `app.modules.dicom_support.read_transfer_syntax`, never from
`Dataset.original_encoding` or anything pydicom infers, and compared with the allow-list of five UIDs; any
other UID, a missing (0002,0010), a missing preamble or an unreadable group 0002 is refused, never guessed.
The order of the checks is stored size, transfer syntax, inflated size (Deflated only), declared decoded size,
decode. The inflated size of a Deflated object is counted with a bounded decompressor (64 KiB input and at
most 64 KiB output per step, output discarded), stops as soon as the count exceeds
`dicom_max_decoded_bytes` and never holds more than the bound plus one chunk; a `zlib` error or a truncated
stream is a decode failure. Without `frame` nothing is checked (SR-017 AC 8). The real-decode fixtures
(NumPy installed, TASK-233) are built in memory in `backend/modules/dicom_viewer/tests/fixtures.py`.

## Verification results

TC-019.1 to TC-019.5: see TASK-218 "Implementation record (Software Developer, 2026-11-13)" and TASK-226.
TC-019.6 to TC-019.8: see TASK-234 "Implementation record" and "Implementation record, round 2" (2026-11-25).
TC-019.12: see TASK-237 "Implementation record".

## Version history

- 1.0 (2026-11-13): TASK-218. Created for SR-017 AC 6 (TC-019.1 to TC-019.4). `in_review`.
- 1.0 (2026-11-13): QA review of TASK-218 (round 2): `approved` (status only; content unchanged).
- 1.1 (2026-11-15) — TASK-226 (CR-006 verification): TC-019.5 added (real render on a started stack), recorded as not executable (PRB-048, PRB-046); TC-019.1 to TC-019.4 re-run green. Content change on an approved record, so the approval record is cleared: `in_review`.
- 1.1 (2026-11-15) — QA review of TASK-226 (round 2): `approved` (status only; content unchanged).
- 1.2 (2026-11-25) — TASK-237 (CR-008 D-5; PRB-048): TC-019.12 added (SR-017 AC 11, no viewer control, Download kept). Content change on an approved record, so the approval record is cleared: `in_review`.
- 1.3 (2026-11-25) — TASK-234 (CR-008, PRB-046), applied on top of 1.2 (TASK-237). Added TC-019.6 (transfer-syntax refusal, missing syntax, private-API pin; SR-017 AC 10), TC-019.7 (Deflated bomb and corrupt stream; AC 6) and TC-019.8 (order of the checks; AC 6, AC 10); unit acceptance extended. Content change, so the approval record stays cleared: `in_review`.
- 1.4 (2026-11-25) — TASK-234 QA round 1 (R1-1 to R1-4). Preconditions and Scope brought up to date (branch, NumPy installed, real fixtures, helper under test, SR-017 AC 11, SI-FE-CORE `AttachmentItem` and the frontend environment); TC-019.12 names its two `ClinicalEntriesPage.test.tsx` tests; TC-019.6 adds the unconvertible (0002,0010) and invalid-UID cases; TC-019.7 adds valid Deflated objects over one chunk with and without the pad byte and the bounded-read assertion; Verification results point at TASK-234 and TASK-237. Still `in_review`.
- 1.4 (2026-11-25) — QA review of TASK-234 (round 2): TC-019.6 to TC-019.8 approved; TC-019.12 approved by the TASK-237 QA: `approved` (status only; content unchanged).
