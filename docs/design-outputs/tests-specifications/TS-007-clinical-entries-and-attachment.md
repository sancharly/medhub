---
id: TS-007
type: test-specification
title: Clinical entries and attachment verification
status: approved
version: "1.4"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-31"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-31"
approved_digest: efbaa0fe49fd538ac378760f773b4f4540944001406cf4e19bc34f668296f468
approval_note: self-approved
links:
  - target: SR-012
    relation: verifies
  - target: SR-013
    relation: verifies
tags:
  - level:unit
  - class:B
---

# TS-007 — Clinical entries and attachment verification

## Scope

Software requirements covered: SR-012, SR-013.
Software items under test: SI-CLINICAL, SI-ATTACH, SI-FE-CORE.
Levels: unit, integration.

## Preconditions and environment

Build: branch `bug/soup-pinning` (CR-001), which holds `backend/tests/test_object_storage.py` (TC-007.5); branch `bug/minio-object-store` (CR-002) for TC-007.6 to TC-007.8. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 24 LTS (build stage node:24.22.2-trixie-slim; CI node-version 24) with `frontend/package-lock.json`.
Unit and service tests run with no external services (in-memory repositories and a fake object store). TC-007.5 builds the real boto3 S3 client from the locked SDK; no object-storage service is needed. TC-007.6 (audit persistence) is *real DB*. Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-007.1 | SR-012 | `backend/tests/clinical/test_clinical_service.py`, `backend/tests/api/test_clinical_router.py` | Required fields are enforced and the author comes from the session, not the payload | A forged author field is ignored |
| TC-007.2 | SR-013 | `backend/tests/attachments/test_attachment_upload.py`, `backend/tests/attachments/test_dicom_validation.py` | Uploads are validated, size-limited and bound to the entry and patient transactionally | An invalid or oversized object is rejected without a dangling row |
| TC-007.3 | SR-013, SR-005 | `backend/tests/attachments/test_attachment_fetch.py`, `backend/tests/api/test_attachments_router.py` | Fetching an attachment requires authorization for the owning entry | Unauthorized fetch denied |
| TC-007.4 | SR-012, SR-013 | `frontend/src/core/clinical/ClinicalEntriesPage.test.tsx` | Entries and their attachments render for the authorized viewer with correct attribution | Author name shown per entry author, not per viewer |
| TC-007.5 | SR-013 (AC-3) | `backend/tests/test_object_storage.py::test_object_storage_client_builds_real_s3_client` | The object-storage client is built from the declared SDK: `ObjectStorageClient()` imports the real `boto3` (no patch, stub or `importorskip`) and builds an S3 client for the configured endpoint and bucket, with no reachable endpoint | Test passes with the real `boto3` import; it fails with `ImportError` when `boto3` is not installed |
| TC-007.6 | SR-013 (AC-5) | `backend/tests/attachments/test_attachment_fetch.py::test_open_substituted_object_is_refused_and_audited_as_failure`, `backend/tests/api/test_attachments_router.py::TestFetchSubstitutedAttachment`, `backend/tests/attachments/test_attachment_integrity_persistence.py` (*real DB*) | An attachment whose stored bytes differ from the SHA-256 recorded at upload is not served: the service raises `AttachmentIntegrityError`, the API answers 502 `application/problem+json` (type `attachment-integrity-failure`) whose detail names the attachment id and carries no hash or content, and an `ATTACHMENT_ACCESS` audit event with outcome FAILURE for the attachment and actor is committed and still present after the failed request | No object bytes in the response; 502 problem; FAILURE audit row found in a fresh session after the request. Each test fails when the checksum comparison is removed (the persistence test also fails when the FAILURE event is written back into the request transaction, ADR-0016) |
| TC-007.7 | SR-013 (AC-5) | `backend/tests/attachments/test_attachment_fetch.py::test_open_unmodified_object_returns_identical_bytes_and_audits_success`, `backend/tests/attachments/test_attachment_fetch.py::test_doctor_with_consent_can_open_attachment` | An unmodified object downloads with identical bytes and a SUCCESS `ATTACHMENT_ACCESS` audit event | Bytes equal the uploaded bytes; audit outcome SUCCESS |
| TC-007.8 | SR-013 (AC-5) | `backend/modules/dicom_viewer/tests/test_studies_endpoint.py::TestSubstitutedDicomObject` | A DICOM attachment fetched through the viewer route (`/studies/{attachment_id}`) with a substituted object is refused with 502 and no DICOM content; the FAILURE audit event is recorded | 502 problem; `stream_dicom` is never called; FAILURE audit for the attachment and actor |

## Acceptance criteria (class B unit level, §5.5.3)

- Data flow: the object is written before the metadata commit, so a failure leaves no dangling reference.
- Resource allocation: uploads must not be buffered whole in memory (currently PRB-008).
- Boundary: attachment exactly at the size limit.
- Fault handling: an object whose SHA-256 differs from the stored checksum is never returned, on any download path including DICOM (SR-013 AC 5).

## Notes

Streaming upload and download (TASK-135) is open; TC-007.2 verifies the limit, not the memory profile.

## Version history

- 1.1 (2026-10-22) — CR-001 (TASK-157, PRB-002): test case TC-007.5 for SR-013 AC-3, so a missing
  object-storage SDK fails the build. Test cases TC-007.1 to TC-007.4 unchanged. TASK-158 (QA
  follow-up of TASK-157): preconditions name `bug/soup-pinning` as the build of TC-007.5 and state
  that TC-007.5 builds the real boto3 S3 client and needs no object-storage service.
- 1.3 (2026-10-30) — CR-002 (TASK-173, PRB-043): test cases TC-007.6 to TC-007.8 verify SR-013 AC 5
  (stored SHA-256 checked on every download, including DICOM). Content change, so the approval is
  cleared and the record returns to review. Test cases TC-007.1 to TC-007.5 unchanged. Mutation
  check recorded in TASK-173.
- 1.4 (2026-10-30) — CR-002 (TASK-183, PRB-052, QA review): TC-007.6's pass criterion no longer
  cites TASK-173's `durable` commit, which TASK-183 removed. The FAILURE row is now committed by
  `AuditService` on its own transaction (ADR-0016); the persistence test is unchanged apart from its
  cleanup and runs without `durable`. Content change, so the record returns to review for the human.
