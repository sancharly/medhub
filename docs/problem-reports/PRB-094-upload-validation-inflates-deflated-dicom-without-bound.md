---
id: "PRB-094"
type: problem-report
title: "DICOM upload validation inflates a Deflated object without a bound"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-25"
updated: "2026-11-26"
criticality: major
links: []
tags: ["hazard:availability", "dicom", "security", "found-in:CR-008-plan"]
---

# PRB-094 — DICOM upload validation inflates a Deflated object without a bound

## Observed

Found at the CR-008 Plan stage (Software Architect role, 2026-11-25) while re-reviewing the published
source of pydicom 3.0.2 for SOUP-015 1.3. Established statically from the MedHub source and pydicom's
published source; not reproduced (no crafted object was run against the API).

Every upload of a file sent as `application/dicom`, or named `*.dcm`, is validated by
`pydicom.dcmread(fp, stop_before_pixels=True)`. For an object whose transfer syntax is Deflated Explicit VR
Little Endian (`1.2.840.10008.1.2.1.99`), pydicom inflates the whole data set in memory with no output
limit before `stop_before_pixels` applies. Deflate reaches ratios of about 1000:1, so an upload within the
150 MiB attachment maximum can ask the API process for on the order of 150 GiB.

## Investigation

1. `POST /api/v1/clinical-entries/{entry_id}/attachments` (`backend/app/api/routers/attachments.py:103-112`)
   passes the spooled upload to `AttachmentService.store` (`backend/app/attachments/service.py:46-54`).
   The body is already bounded to 150 MiB stored (SR-013 AC 6, CR-006).
2. `service.py:100-106`: `is_dicom` is true for content type `application/dicom` or a `.dcm` file name;
   `validate_dicom(file)` is then called on the spooled file.
3. `backend/app/attachments/dicom_validation.py:19`: `pydicom.dcmread(fp, stop_before_pixels=True)`.
4. pydicom 3.0.2 `src/pydicom/filereader.py:891-906` (tag `v3.0.2`, published source read only): for the
   Deflated UID, `zipped = fileobj.read()` then `zlib.decompress(zipped, -zlib.MAX_WBITS)` with no
   `max_length`, and the data set is parsed from the inflated buffer. `stop_before_pixels` stops the parse,
   not the inflation.

Root cause: MedHub's memory bound on uploads (SR-013 AC 6: content handled in bounded chunks) assumes that
validation reads a bounded header. That holds for every transfer syntax except Deflated, where the SOUP
expands the whole object first. The same pydicom property affects the DICOM module's frame path, which
CR-008 makes reachable; TASK-234 bounds it there.

## Impact

Availability. One crafted upload makes the API worker that handles it allocate until the container's
memory limit, so the worker is killed (or the host swaps): in-flight requests on it fail and uploads and
reads are delayed until it restarts (RISK-007). Several such uploads can keep the API down. Reachable today
by any authenticated user allowed to upload an attachment (a doctor with access to the entry); no module
needs to be installed. The stored data is not changed: the failed upload stores nothing.

## Safety evaluation

- No data is disclosed, altered or misattributed: the failure is before `put_object` and before the record
  is written (`service.py:108-121`). No wrong image is shown (RISK-003 not affected).
- Contributes to RISK-007 (clinical information unavailable): a worker crash delays access to every
  record, not only to the attachment. Also a security weakness (denial of service by an authenticated
  insider), with no confidentiality or integrity effect.
- Criticality **major**: one request from an ordinary authenticated user can take down an API worker, by a
  path the existing controls were meant to bound (SR-013 AC 6). Not `critical`: it needs an authenticated
  user with upload rights, it is recoverable by a restart, and no data is lost or wrong.
- Released versions (§9.3): no `release` record exists, so no released version in use is affected and no
  notification is needed.

## Resolution

Resolved in CR-008 (D-B; the `resolves` link is on CR-008), verified in the working tree on 2026-11-26 (TASK-239, branch `bug/dicom-module-install`, head 5bd10e7 plus the task's working-tree changes).

What changed: **TASK-240**. `validate_dicom` (`backend/app/attachments/dicom_validation.py`) reads the transfer syntax from the file meta information and, for Deflated Explicit VR Little Endian, runs `check_inflated_size` (the bounded helper of `backend/app/modules/dicom_support.py`, TASK-234) against `dicom_max_decoded_bytes()` before `pydicom.dcmread`; above the bound it raises a 400 `ValidationProblem`, rule `dicom_decoded_size_exceeded`, and nothing is stored. Other syntaxes are unchanged. A valid Deflated upload within the bound is still inflated whole by pydicom, up to about 1 GiB (RISK-007, CR-008 Q-2).

Verification (2026-11-26):
- TS-007 TC-007.18, `backend/tests/attachments/test_dicom_validation.py`: 14 passed; the within-bound and other-syntax tests now assert the returned Modality, PatientID and StudyDate values (TASK-240 QA-2).
- Negative control: with the inflation check removed, `test_deflate_bomb_upload_refused_and_nothing_stored` and `test_deflate_bomb_through_validate_dicom_on_a_spooled_file` fail; restored, all 14 pass.
- Started stack: a 1 044 152-byte Deflated upload inflating above 1 GiB, sent by a doctor with access, answered 400 `dicom_decoded_size_exceeded` in 1.8 s; the backend container stayed at 152 to 153 MiB (idle 152 MiB, `docker stats`), `RestartCount` 0, no OOM kill, one "Booting worker" line in the log (the start), and no attachment row was created; a small valid Deflated upload was accepted and downloaded byte-identical.
- Hosted CI: the Docker Build job (including the TASK-236 image check) and the full workflow run only after the human approves a push; their result is verified on hosted CI after push and is not claimed here.

## Source

pydicom 3.0.2 published source (`filereader.py`, tag `v3.0.2`) and MedHub `HEAD` 396e9de: the file and line
references above. SOUP-015 1.3 "Review of 2026-11-25".

## Version history

- 1.0 (2026-11-25) — Created at the CR-008 Plan stage (Software Architect role); taken into CR-008 (D-B).
- 1.1 (2026-11-25) — TASK-240 implemented and handed to QA; status unchanged (`open`).
- 1.2 (2026-11-26) — Resolved (TASK-239, CR-008): "Not fixed yet" replaced by the Resolution above. The human closes the PRB in MedTrace after the merge.
