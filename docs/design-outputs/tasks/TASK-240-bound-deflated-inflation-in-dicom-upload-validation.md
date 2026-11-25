---
id: "TASK-240"
type: task
title: "Bound the inflation of Deflated DICOM uploads before validation reads them"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-25"
updated: "2026-11-25"
links:
  - target: "SR-013"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-008"
    relation: relates_to
  - target: "PRB-094"
    relation: relates_to
  - target: "TASK-234"
    relation: relates_to
  - target: "ADD-012"
    relation: relates_to
  - target: "SOUP-015"
    relation: relates_to
  - target: "TS-007"
    relation: relates_to
tags: ["cr:CR-008", "control:protective", "backend"]
---

# TASK-240 — Bound the inflation of Deflated DICOM uploads before validation reads them

- **Software items / units:** SI-ATTACH `U-ATT-Upload` (`backend/app/attachments/dicom_validation.py`;
  ADD-012), using the shared helper `app.modules.dicom_support` from TASK-234.
- **PRB:** PRB-094. **CR:** CR-008 (D-B: upload-path inflation taken into CR-008; the 1 GiB
  `dicom_max_decoded_bytes` setting reused, no new setting).
- **Requirement:** SR-013 AC 6 (uploads are not held whole in the API process's memory; content in
  bounded chunks). Inflating a Deflated upload without a bound breaks that criterion, so no new AC is
  needed. Not SR-017 (the module) and not SR-026 (performance budgets).
- **Depends on:** TASK-234 (helper). **Before:** TASK-238, TASK-239. Can run in parallel with TASK-235
  and TASK-236.
- **Size:** S (`dicom_validation.py`, `backend/tests/attachments/test_dicom_validation.py` or the existing
  upload test file; records).

## Objective

Before `pydicom.dcmread` reads an uploaded DICOM file, `validate_dicom`:

1. reads the transfer syntax with `read_transfer_syntax(fp)`;
2. if it is Deflated Explicit VR Little Endian, calls `check_inflated_size(fp, dicom_max_decoded_bytes())`:
   - above the bound, the upload is refused with an RFC 7807 400 (`ValidationProblem`), field `file`,
     rule `dicom_decoded_size_exceeded`, message naming the limit in bytes;
   - a corrupt deflate stream is refused as an invalid DICOM file, with the existing `ValidationProblem`
     shape;
3. otherwise behaves exactly as today. Upload validation does **not** apply the frame-path allow-list:
   any transfer syntax may be stored (SR-017 AC 8 serves it whole).

Nothing is stored for a refused upload (the check runs before `put_object`, `service.py:100-110`). `fp` is
at offset 0 afterwards, as today. Memory stays bounded by the helper's chunk sizes. A legitimate
Deflated upload within the bound is still inflated in full by pydicom, up to about 1 GiB. That is the same
peak the frame path accepts (CR-008 Q-2), and it is recorded in RISK-007.

## Steps

Test first: the bomb test must fail on `HEAD` + TASK-234. To show it failing without exhausting memory,
monkeypatch `dicom_max_decoded_bytes` to 1 MiB and assert that `zlib.decompress` is never called with the
full stream (spy). Do not run a real 150 MiB bomb.

1. Tests, `backend/tests/attachments/test_dicom_validation.py` (new, or next to the existing upload tests),
   using `validate_dicom` directly and through `AttachmentService.store` with the existing fakes:
   - `test_deflate_bomb_upload_refused_and_nothing_stored`: a valid file meta information with the Deflated
     UID, followed by a raw deflate stream of zeros that inflates above the (patched) bound. Expect a 400
     `ValidationProblem` with rule `dicom_decoded_size_exceeded` naming the limit. Expect also: the spy shows
     `pydicom.dcmread` never called, and the storage fake's `put_object` never called.
   - `test_deflated_upload_within_bound_is_accepted`: a small valid Deflated object (from the pydicom writer,
     as in TASK-234's fixtures, copied or shared through a test helper in `backend/tests`; the host's
     tests must not import the module's test package). The metadata dict is returned as today, and the file
     offset is 0.
   - `test_corrupt_deflate_stream_upload_refused`: a 400 invalid-DICOM problem; nothing stored.
   - `test_non_deflated_upload_unchanged`: an Explicit VR Little Endian and a JPEG Baseline object are
     accepted with the same metadata as on `HEAD`, and the helper's inflation check is not called.
2. `dicom_validation.py`: implement the Objective; import `read_transfer_syntax`, `check_inflated_size`,
   and their exceptions from `app.modules.dicom_support`, the Deflated UID
   `DeflatedExplicitVRLittleEndian` from `pydicom.uid` (TASK-234 kept it out of the helper; TASK-234 QA
   R1-5), and
   `dicom_max_decoded_bytes` from `app.modules.module_settings`. Make no other change in `backend/app`.
3. Records (in the same commit):
   - **TS-007** (approved 1.13 → 1.14, set to `in_review`, remove `approved_by`, `approved_on`,
     `approved_digest` and `approval_note`): add **TC-007.18**. It verifies SR-013 AC 6, covers the four
     step-1 tests, and fails on `HEAD` (spy: unbounded `zlib.decompress` called). Add a unit acceptance
     line: a Deflated upload is inflated under the decoded bound before validation; other syntaxes are
     unchanged. Add a version-history line.
   - RISK-007's upload-path row already names TASK-240 and TC-007.18 as planned. TASK-239 records the
     executed result.

## Verification

- `cd backend && uv run pytest tests/attachments tests/modules tests/api/test_attachments_router.py -q`,
  then the whole suite with `uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=85`.
- `uv run ruff check . && uv run black --check . && uv run mypy app` (CI runs Black).
- `cd backend && uv run python -m app.export_openapi --output openapi/openapi.json && git diff --exit-code openapi/openapi.json`:
  no diff is expected, because the upload's 400 response is already documented. If a diff appears, follow
  the CLAUDE.md contract workflow.
- Mutation checks, recorded in the Implementation record:
  - (a) remove the inflation check: the bomb test fails (its spy sees full inflation).
  - (b) apply the check to every syntax: `test_non_deflated_upload_unchanged` fails.
  - (c) read the syntax after `dcmread`: the bomb test fails.
- Run `traceability-check` on TASK-240, TS-007, PRB-094 and CR-008 (0 errors), then `graphify update .`.

## Acceptance criteria

- [x] A Deflated upload that inflates above `dicom_max_decoded_bytes` is refused with a 400 problem (rule
  `dicom_decoded_size_exceeded`) without being fully inflated, and nothing is stored (SR-013 AC 6;
  TC-007.18).
- [x] Valid Deflated uploads within the bound, and uploads in every other transfer syntax, are accepted as
  before. A corrupt deflate stream is an invalid-DICOM 400 (TC-007.18).

## Definition of Done

- [x] Tests written first and seen failing; the suites, Ruff, Black and mypy are green; mutation checks
  recorded.
- [x] TS-007 updated; `traceability-check` reports 0 errors; `graphify update .` run.

## Implementation record

- `backend/app/attachments/dicom_validation.py`: `_check_deflated_size(fp)` runs before `dcmread`. It reads the
  syntax with `read_transfer_syntax`, and only for `pydicom.uid.DeflatedExplicitVRLittleEndian` calls
  `check_inflated_size(fp, dicom_max_decoded_bytes())`. `InflatedSizeExceeded` becomes a 400
  `ValidationProblem` (field `file`, rule `dicom_decoded_size_exceeded`, message naming the limit);
  `DeflateStreamError` becomes the existing "Invalid DICOM file: ..." 400. No other change in `backend/app`.
- `fp` is the route's `SpooledTemporaryFile` (`file.file`): seekable, read in chunks of at most 64 KiB by the
  helper. A Deflated upload within the bound is still read and inflated whole by pydicom 3.0.2 in
  `dcmread`, up to about 1 GiB: the residual accepted in RISK-007 (CR-008 Q-2). *(Corrected at commit per
  QA-1; the earlier wording said "never whole".)*
- Tests, `backend/tests/attachments/test_dicom_validation.py` (14 in the file, 10 new cases): bomb through
  `AttachmentService.store` and through `validate_dicom` on a spooled file (read sizes <= 64 KiB), within-bound
  accepted, over-one-chunk with and without pad byte (under `call_with_timeout`), corrupt stream, malformed
  (0002,0010) VR `ZZ` and wrong-length `UV` (400, no 5xx), non-Deflated unchanged. Fixtures are loaded by path
  from the module's `tests/fixtures.py`, as `tests/modules/test_dicom_support.py` does.
- Red on `HEAD` d576494: the bomb tests failed with "DID NOT RAISE ValidationProblem" (bomb accepted and
  inflated in full by pydicom); the non-Deflated test failed for want of the helper import.
- Mutation checks: (a) check removed: 2 failed (both bomb tests); (b) check applied to every syntax: 2 failed
  (`test_non_deflated_upload_unchanged` x2); (c) syntax read after `dcmread`: 1 failed
  (`test_deflate_bomb_upload_refused_and_nothing_stored`). Restored: 14 passed.
- Verification: attachments + modules + attachments router 247 passed; full suite 1775 passed, 10 skipped,
  coverage 95.24%; Ruff, Black, mypy (138 files) clean; OpenAPI export: no diff.

## QA review — round 1 (2026-11-25): APPROVED

Re-run by QA on the working tree of `bug/dicom-module-install` (HEAD d576494 + this task's changes): attachments +
modules + attachments router 247 passed; full suite 1775 passed, 10 skipped, coverage 95.24%
(`dicom_validation.py` 100%); Ruff check and format, Black and mypy (138 files) clean; OpenAPI export identical to
the committed file. `traceability-check` (scope CR-008 tag, CR-008, TASK-240, TS-007, PRB-094, RISK-007, SR-013;
109 records): 0 errors.

- **Fixtures stand alone.** Every helper the tests use exists in `HEAD:backend/modules/dicom_viewer/tests/fixtures.py`;
  with that HEAD copy in a scratch tree the file gives 14 passed.
- **Router probe** (`create_app()`, real `AttachmentService`, mocked storage and repository): a bomb against a 1 MiB
  bound, and a real 1.1 GiB bomb at the default 1 GiB bound (0.43 s, tracemalloc peak 4.2 MiB), answer 400
  `application/problem+json`, `errors[0].rule` `dicom_decoded_size_exceeded`, the limit named; no `put_object`, no
  `add`, no audit. The stream is the route's `SpooledTemporaryFile` (rolled to disk for the large bomb), read in at
  most 64 KiB. ZZ and UV (0002,0010), ZZ with the Deflated UID, a corrupt and a truncated stream are 400
  "Invalid DICOM file"; none gives a 5xx. Pad-byte and no-pad-byte objects over one chunk, and 40 Deflated
  256-row objects (columns 200 to 239), are accepted with no hang; 2,000 single-byte mutations of Deflated objects
  give only accepted or 400.
- **Non-Deflated unchanged.** `validate_dicom` against the HEAD version over 3,009 inputs (Explicit/Implicit LE,
  Big Endian, no (0002,0010), JPEG Baseline, RLE, non-DICOM, 3,000 mutations): 0 differences in result, message
  or final offset.
- **Mutations** (scratch copy): (a) check removed: 2 failed (both bomb tests); (c) check after `dcmread`: 1 failed;
  (b) check on every syntax (`if False:`): 5 failed; `DeflateStreamError` not mapped: 1 failed. Restored: 14 passed.
- **RISK-007 control** (row "Deflated DICOM uploads inflated with the same bounded helper"): implemented and tested
  by TC-007.18; the executed result is TASK-239's.

Findings (none blocking):

- **QA-1 MEDIUM.** The Implementation record says the upload is "never whole (SR-013 AC 6 holds; no conflict)". That
  holds for the helper only. For a Deflated upload within the bound, pydicom 3.0.2 still reads the whole object
  (`filereader.py:898`, `fileobj.read()`) and inflates it in full (`:903`), up to about 1 GiB, as the Objective and
  RISK-007 state. Fix: reword the bullet to "the helper reads in chunks of at most 64 KiB; a Deflated upload within
  the bound is still read and inflated whole by pydicom, the residual accepted in RISK-007 (CR-008 Q-2)", in TASK-239's
  record update or at commit time.
- **QA-2 LOW.** `test_deflated_upload_within_bound_is_accepted` and `test_non_deflated_upload_unchanged` check the
  key set only, while TC-007.18 says "the same metadata". Fix: assert the values (`Modality`, `PatientID`,
  `StudyDate` of the built data set). QA's HEAD-equivalence run covers it for this review.

Pre-existing (not blocking): `_read_file_meta_info` reads group 0002 values whole (bounded by the 150 MiB attachment
limit), now up to three times in sequence for a Deflated upload; HEAD's `dcmread` already did so once.

## Version history

- 1.0 (2026-11-25) — Created after the CR-008 Plan gate (Software Architect role) from D-B (Q-1: the
  upload-path inflation is taken into CR-008; Q-2: same 1 GiB setting). `draft`.
- 1.1 (2026-11-25) — Step 2 takes the Deflated UID from `pydicom.uid`, not the helper, which does not
  define it (TASK-234 QA R1-5; orchestrator). `draft`.
- 1.2 (2026-11-25) — Implemented; TS-007 1.14 (TC-007.18). `draft → in_review` (Software Developer role).
- 1.2 (2026-11-25, QA) — Round 1 APPROVED (QA-1 MEDIUM, QA-2 LOW, not blocking). Status `approved`.
