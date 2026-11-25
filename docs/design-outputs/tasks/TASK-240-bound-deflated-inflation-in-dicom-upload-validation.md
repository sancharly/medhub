---
id: "TASK-240"
type: task
title: "Bound the inflation of Deflated DICOM uploads before validation reads them"
status: draft
version: "1.0"
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
   their exceptions and `DEFLATED_EXPLICIT_VR_LITTLE_ENDIAN` from `app.modules.dicom_support`, and
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

- [ ] A Deflated upload that inflates above `dicom_max_decoded_bytes` is refused with a 400 problem (rule
  `dicom_decoded_size_exceeded`) without being fully inflated, and nothing is stored (SR-013 AC 6;
  TC-007.18).
- [ ] Valid Deflated uploads within the bound, and uploads in every other transfer syntax, are accepted as
  before. A corrupt deflate stream is an invalid-DICOM 400 (TC-007.18).

## Definition of Done

- [ ] Tests written first and seen failing; the suites, Ruff, Black and mypy are green; mutation checks
  recorded.
- [ ] TS-007 updated; `traceability-check` reports 0 errors; `graphify update .` run.

## Version history

- 1.0 (2026-11-25) — Created after the CR-008 Plan gate (Software Architect role) from D-B (Q-1: the
  upload-path inflation is taken into CR-008; Q-2: same 1 GiB setting). `draft`.
