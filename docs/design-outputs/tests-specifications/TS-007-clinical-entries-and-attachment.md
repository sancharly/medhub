---
id: TS-007
type: test-specification
title: Clinical entries and attachment verification
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-22"
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

Build: branch `bug/soup-pinning` (CR-001), which holds `backend/tests/test_object_storage.py` (TC-007.5). Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 20 with `frontend/package-lock.json`.
Unit and service tests run with no external services (in-memory repositories and a fake object store). TC-007.5 builds the real boto3 S3 client from the locked SDK; no object-storage service is needed. Tests marked *real DB* require a
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

## Acceptance criteria (class B unit level, §5.5.3)

- Data flow: the object is written before the metadata commit, so a failure leaves no dangling reference.
- Resource allocation: uploads must not be buffered whole in memory (currently PRB-008).
- Boundary: attachment exactly at the size limit.

## Notes

Streaming upload and download (TASK-135) is open; TC-007.2 verifies the limit, not the memory profile.

## Version history

- 1.1 (2026-10-22) — CR-001 (TASK-157, PRB-002): test case TC-007.5 for SR-013 AC-3, so a missing
  object-storage SDK fails the build. Test cases TC-007.1 to TC-007.4 unchanged. TASK-158 (QA
  follow-up of TASK-157): preconditions name `bug/soup-pinning` as the build of TC-007.5 and state
  that TC-007.5 builds the real boto3 S3 client and needs no object-storage service.
