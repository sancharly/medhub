---
id: "TASK-217"
type: task
title: "Bound two-pass attachment download that serves only verified bytes"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-13"
links:
  - target: "SR-013"
    relation: implements
  - target: "SR-026"
    relation: implements
  - target: "RISK-012"
    relation: mitigates
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-008"
    relation: relates_to
  - target: "ADD-012"
    relation: relates_to
  - target: "SOUP-036"
    relation: relates_to
  - target: "SOUP-019"
    relation: relates_to
  - target: "TS-007"
    relation: relates_to
  - target: "TASK-135"
    relation: relates_to
tags: ["cr:CR-006", "control:design", "control:protective"]
---

# TASK-217 — Bound two-pass attachment download that serves only verified bytes

- **Software item / unit:** SI-ATTACH `U-ATT-Fetch` (ADD-012); SI-API attachment router (ADD-005);
  `ObjectStorageClient`.
- **PRB:** PRB-008 (download half). **CR:** CR-006 (D-6, D-10 / R-1; ADR-0021).
- **Depends on:** TASK-135 (same service and router files; commit after it). **Step 1 runs first in the
  Build stage**, before any CR-006 code, because its result can change the plan (D-10 fallback).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** M (`backend/app/attachments/service.py`, `backend/app/core/object_storage.py`,
  `backend/app/api/routers/attachments.py`; tests `backend/tests/attachments/`,
  `backend/tests/test_object_storage.py`; records TS-007, SOUP-036, SOUP-019).
- **Needs:** a Docker daemon (step 1 and the real-store test).

## Objective

SR-013 AC 6 (download half) and AC 5 together: content is served in bounded chunks and every byte served
was verified against the stored SHA-256. Today `open()` reads the whole object into memory
(`ObjectStorageClient.get_object` → `Body.read()`, `service.py:158`) and `fetch_attachment` re-chunks it.

## Steps

1. **Confirm SOUP-036 behaviour 14 on the pinned store** (D-10). Against
   `chrislusf/seaweedfs:4.51@sha256:f7a49e3f…134b8` started as in `infra/docker-compose.yml` (SSE-S3 on,
   bucket default AES256), with boto3 1.43.117 built as `ObjectStorageClient` builds it: put an object;
   `get_object` returns an `ETag`; `get_object(IfMatch=etag)` returns the bytes; overwrite the object;
   `get_object(IfMatch=old_etag)` raises `ClientError` `PreconditionFailed` (HTTP 412) with no body; a
   wrong-quoted or unquoted ETag behaves as the code will send it. Record the commands and output in
   SOUP-036 ("Functional and performance requirements", item 14) and here. **If any check fails, stop**
   and report to the coordinator: the D-10 fallback (SR-013 AC 5 change, RISK-012 4 × 2 → alarp) is the
   human's decision.
2. **Object store client:** `get_object_stream(key, if_match=None) -> (Iterator[bytes], etag)` over
   `Body.iter_chunks(65536)`; the response is opened before the iterator is returned, so a 412 raises
   before the caller starts a response. Map `PreconditionFailed` to a dedicated `ObjectChangedError`.
3. **Service:** `open_stream(actor, attachment_id) -> (Iterator[bytes], content_type, filename, size)`:
   authorize; pass 1 hashes chunks keeping nothing and records the ETag; constant-time compare; on a
   mismatch, the existing AC 5 path (FAILURE row on its own transaction, `AttachmentIntegrityError` → 502).
   On a match, pass 2 `get_object_stream(key, if_match=etag)`; `ObjectChangedError` → the same AC 5 path.
   Record the SUCCESS `ATTACHMENT_ACCESS` row once pass 2 is open. Return a generator that hashes while
   yielding; after the last chunk, if the digest differs, record a FAILURE row and raise (the server aborts
   the connection; the chunked body is never completed).
4. **`open()` for the module path** stays (bytes, verified) and gains `max_bytes: int | None = None`:
   when set and `attachment.size > max_bytes`, raise the SR-017 AC 6 problem before reading (used by
   TASK-218; tests here cover the refusal only).
5. **Router:** `fetch_attachment` uses `open_stream`; `Content-Length` set from `attachment.size`;
   `Content-Disposition` unchanged (TASK-204/206).
6. Update SOUP-019 if the relied-on text differs from what was exercised.

## Tests (write first)

- `test_download_memory_bounded` (SR-013 AC 6): `tracemalloc` peak while consuming a 20 MiB download stays
  under a fixed bound, for two sizes.
- `test_download_reads_object_twice_second_conditional` (SR-013 AC 5, D-10): fake store records calls:
  pass 2 carries `IfMatch` equal to pass 1's ETag.
- `test_download_object_replaced_between_passes_gives_502_and_failure_row` (SR-013 AC 5; RISK-012): fake
  store raises `PreconditionFailed` on pass 2; response 502 problem, no content bytes, one FAILURE row,
  no SUCCESS row.
- `test_download_mismatch_in_second_pass_aborts` (SR-013 AC 5): pass 2 yields different bytes; the client
  sees an incomplete transfer (exception / truncated body), a FAILURE row is recorded.
- `test_open_max_bytes_refuses_before_read` (SR-017 AC 6 interface): no `get_object` call.
- Real store (Docker, marked like the other real-service tests): replaced-object case on SeaweedFS 4.51.
- Existing TC-007.6 to TC-007.8 (checksum) pass unchanged.
- Recorded in TS-007 (TC-007.10, TC-007.11; same version as TASK-135's change).

## Acceptance criteria

- [ ] SOUP-036 behaviour 14 confirmed by a run on the pinned digest (or the task stopped with the result).
- [ ] SR-013 AC 6 (download): memory bounded independently of object size.
- [ ] SR-013 AC 5: no unverified byte is served; replaced object → 502, FAILURE row, no content; second-pass
  mismatch → transfer aborted and FAILURE row.

## Definition of Done

- [ ] `ruff`, `mypy`, backend suite green; OpenAPI export byte-identical
- [ ] TS-007, SOUP-036 (evidence of step 1), SOUP-019 updated; `traceability-check` no error for this record

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect) from the download half of
  TASK-135 1.2, with the D-10 binding and the SOUP-036 confirmation as its first step.
