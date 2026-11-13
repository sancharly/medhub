---
id: "TASK-217"
type: task
title: "Bound two-pass attachment download that serves only verified bytes"
status: approved
version: "1.6"
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

- [x] SOUP-036 behaviour 14 confirmed by a run on the pinned digest (or the task stopped with the result).
- [x] SR-013 AC 6 (download): memory bounded independently of object size.
- [x] SR-013 AC 5: no unverified byte is served; replaced object → 502, FAILURE row, no content; second-pass
  mismatch → transfer aborted and FAILURE row.

## Definition of Done

- [x] `ruff`, `mypy`, backend suite green; OpenAPI export byte-identical
- [x] TS-007, SOUP-036 (evidence of step 1), SOUP-019 updated; `traceability-check` no error for this record

## Implementation record (Software Developer, 2026-11-13)

### Step 1 evidence — SOUP-036 behaviour 14 on the pinned image

Throwaway container and network (removed afterwards), image
`chrislusf/seaweedfs:4.51@sha256:f7a49e3f…134b8`, command line and `WEED_S3_SSE_KEY` as in
`infra/docker-compose.yml`, S3 on a loopback host port; bucket created by
`app.core.object_store_init.initialise` (default encryption AES256). Client: boto3/botocore 1.43.117
built as `ObjectStorageClient` builds it (no extra arguments). Output of the probe:

```
bucket enc: [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}, 'BucketKeyEnabled': False}]
ETag '"7f11a7875a8f7bd91f27b68878dd39dc"' SSE AES256 len 200000
iter_chunks bytes 200000
IfMatch quoted -> 200 200000
IfMatch unquoted -> 200 200000
IfMatch bogus ClientError PreconditionFailed 412 'At least one of the pre-conditions you specified did not hold'
new ETag "8df0780d0f392b511bfacd91e48970cc" differs True
IfMatch old after overwrite (quoted) ClientError PreconditionFailed 412 '…'
IfMatch old after overwrite (unquoted) ClientError PreconditionFailed 412 '…'
IfMatch new OK 200 200000
same-content overwrite ETag "8df0780d0f392b511bfacd91e48970cc"
```

Result: all checks pass, so the D-10 fallback is not needed. The code sends the ETag as the store
returned it (quoted); an unquoted one behaves the same. An overwrite with identical bytes keeps the
ETag (a replacement with the same content is harmless: the bytes are the verified ones). The PUT
carried `ServerSideEncryption="AES256"` and the GET reports it. Also exercised by
`backend/tests/integration/test_object_store_conditional_read.py` (`OBJECT_STORE_INTEGRATION=1`;
4 passed against the same container).

### Changes

- `backend/app/core/object_storage.py`: `ObjectChangedError`; `get_object_stream(key, if_match=None)`
  returns `(Iterator[bytes], etag)` over `Body.iter_chunks(65536)`; the response is opened before the
  return and `PreconditionFailed` is mapped to `ObjectChangedError`; the body is closed when the
  iterator ends or is closed.
- `backend/app/attachments/service.py`: `open_stream` (authorise, pass 1 hash and ETag, constant-time
  compare, pass 2 with `if_match`, SUCCESS row once pass 2 is open, generator that hashes while yielding
  and records FAILURE and raises `AttachmentIntegrityError` if the final digest differs); every failure
  before the first byte reuses the existing AC 5 path (`record_access_failure`, 502). `open()` gains
  `max_bytes` (a `ValidationProblem`, 400, before any read); the shared lookup and authorisation moved
  to `_authorized_attachment`.
- `backend/app/api/routers/attachments.py`: `fetch_attachment` streams `open_stream` with
  `Content-Length` from the stored size; `Content-Disposition` unchanged; the in-memory re-chunker and
  `_CHUNK_SIZE` removed (orphaned by this change).
- Tests: `backend/tests/attachments/test_attachment_download.py` (new), `fake_object_store.py` (new
  helper), `backend/tests/test_object_storage.py` (stubbed boto3 client), the real-store file above;
  `test_attachments_router.py` and `test_attachment_integrity_persistence.py` moved to `open_stream` and
  the fake store. TS-007 1.10, TC-007.13 (TC-007.10 and TC-007.11 were already issued by CR-004).

### Acceptance criteria

- SOUP-036 behaviour 14: confirmed by the run above.
- SR-013 AC 6 (download): peak allocation under 4 MiB for 20 MiB and 60 MiB downloads.
- SR-013 AC 5: replaced object gives 502, one FAILURE row and no content; a mismatch in pass 1 gives 502
  after one read; a mismatch at the end of pass 2 aborts the response (Starlette raises "response already
  started" and the server drops the connection) with a FAILURE row.

### Verification

`uv run pytest -q`: 1574 passed, 10 skipped (baseline 1562 passed, 6 skipped; the 4 new skips are the
real-store cases). `uv run ruff check .` clean; `uv run mypy app` clean; `ruff format --check` clean on
the touched files (three untouched test files already needed formatting). OpenAPI export byte-identical
to `backend/openapi/openapi.json`. Mutation check (both applied together, then restored): dropping
`if_match=etag` and disabling the end-of-pass-2 digest check fail
`test_download_reads_object_twice_second_conditional`,
`test_download_object_replaced_between_passes_gives_502_and_failure_row` and
`test_download_mismatch_in_second_pass_aborts` (3 failed, 7 passed); restored, 10 passed. The two
mutations were not run separately.

### Open points for QA and the human

- SOUP-036 (approved 1.4, item 14 says "to be exercised by TASK-217 step 1") and SOUP-019 are approved
  records and were not edited: SOUP-036 needs a 1.5 that records the evidence above (its approval would
  be cleared); SOUP-019's relied-on text (`iter_chunks`, `IfMatch`, 412 `PreconditionFailed`) already
  matches what was exercised, so it needs no change.
- Behaviour of the second-pass abort is "connection dropped, body incomplete", with `Content-Length`
  set so a client can detect a short transfer. The audit trail then has a SUCCESS row (written when pass 2
  opened, in the request transaction) and a FAILURE row for the same download.
- The second pass is by design a second full read of the object (twice the store traffic and latency).

## QA review (qa-engineer, 2026-11-13) — CHANGES REQUESTED

Run by QA: backend `uv run pytest -q` (see the report in the version-history line); `ruff check` clean,
`ruff format --check` clean on touched files (the same 3 pre-existing files); `mypy app` clean; OpenAPI
export byte-identical. Real store, throwaway container of the pinned `chrislusf/seaweedfs:4.51@sha256:f7a49e3f…`
with the Compose command line, an admin identity and `WEED_S3_SSE_KEY`, bucket from
`object_store_init.initialise` (default AES256), removed afterwards: `OBJECT_STORE_INTEGRATION=1` on
`test_object_store_conditional_read.py` and `test_object_store_sse.py`: 8 passed. 150 MiB object, pass 1
then pass 2 with `if_match`: both digests equal, peak Python allocation 0.24 MiB. SOUP-036 1.5 behaviour 14
matches this evidence and the step-1 output above. `traceability-check` (fallback) on CR-006, TASK-217,
TS-007, PRB-008, SOUP-036 and neighbours (78 records): 0 errors; warnings W1 SR-017/SR-026, W5 approved
records → TS-007/SOUP-003/SOUP-036 `in_review`, W6 TASK-176 → obsolete SOUP-022 (pre-existing).

Findings:

1. **[HIGH] A second-pass mismatch is delivered to the client as a complete 200 response.**
   `backend/app/attachments/service.py` `_verified()` yields every chunk, including the last, before it
   checks the digest, and the router sets `Content-Length` to the stored size. By the time the check fails,
   all `Content-Length` bytes have been sent, so dropping the connection is invisible to the client. QA
   probe: real uvicorn, the `test_download_mismatch_in_second_pass_aborts` setup (last byte flipped in
   pass 2), `curl`: `http=200 size=300000`, exit 0, and the file equals the tampered bytes. This breaks
   SR-013 AC 5 ("not served"), ADR-0021 ("the client never sees a complete response") and the RISK-012
   two-pass row; the test only asserts the server-side exception, and the TS-007 fault-handling criterion
   ("aborts the transfer") is not what happens. → Hold the last chunk back: yield each chunk only once the
   next one has been read; when pass 2 is exhausted, compare the digest and yield the held chunk only on a
   match (on a mismatch record FAILURE and raise, so the client gets fewer than `Content-Length` bytes).
   Also refuse if pass 2 delivers more or fewer bytes than `attachment.size`. Make the test observe the
   HTTP side: drive the app at ASGI level and assert the bytes in `http.response.body` messages are fewer
   than `Content-Length` and no final `more_body: False` message is sent (or run uvicorn plus an
   `httpx`/`curl` client and assert a short-read error).
2. **[MEDIUM] The FAILURE row written after the response started is not checked against a real database.**
   `test_attachment_integrity_persistence.py` covers failures before the first byte only; the end-of-stream
   row is written from the threadpool iterator after the endpoint returned. → Add a real-DB case
   (second-pass mismatch: one committed FAILURE row in a fresh session, with the client address) to
   TC-007.13.
3. **[LOW] Audit SUCCESS then FAILURE on a second-pass mismatch: accepted, no human decision needed.**
   ADR-0021 (approved) fixes the SUCCESS row "when pass 2 has been opened (as today: after verification,
   before serving)" and a FAILURE row on a mismatch at the end. Both rows name the same attachment and
   actor, nothing is missing, and the later FAILURE is the accurate final outcome (SR-023, RISK-006). →
   State in TC-007.13 and ADD-012 (TASK-225) that SUCCESS means "verified and serving started" and that an
   aborted transfer adds a FAILURE row.
4. **[LOW] The pass-2 body is closed only by garbage collection when the client disconnects.** Starlette
   does not close a sync iterator on disconnect, so `_chunks()`'s `finally: body.close()` runs when the
   generator is collected (immediately in CPython). → Optional: close the inner iterator in a `finally` in
   `_verified()`.
5. **[LOW, for TASK-136/TASK-226] Two full store reads per download.** Store traffic and time to first byte
   roughly double (a 150 MiB study is read twice before and while sending). Not blocking; TASK-226 should
   measure a large DICOM download against the SR-026 AC 3/AC 5 budgets with 20 clients.

PRB-008: keep `investigating` until this task is approved; then `resolved` (both halves done, CR-006
`resolves` PRB-008), `closed` when CR-006 closes.

## Round 2 (Software Developer, 2026-11-13)

1. **HIGH, fixed.** `_verified()` in `backend/app/attachments/service.py` now holds the last chunk back:
   each chunk is yielded only once the next has been read, and after pass 2 is exhausted the byte count
   (against `attachment.size`) and the SHA-256 are checked before the held chunk is yielded. On a
   mismatch it records FAILURE and raises, so the client receives fewer than `Content-Length` bytes.
   Tests of what the client receives: ASGI level
   (`test_client_never_receives_a_complete_response_when_pass_two_is_tampered`: body shorter than
   `Content-Length`, at most the whole 64 KiB chunks, error raised; the final empty `more_body: False`
   message comes from the `BaseHTTPMiddleware` layers, so "not completed" is not asserted there) and a
   real uvicorn server with an `httpx` client
   (`test_over_http_a_tampered_second_pass_is_a_failed_transfer_not_a_complete_200`: transport error, no
   200 body; control: `test_over_http_an_untouched_object_downloads_completely`).
2. **MEDIUM, done.** `test_failure_audit_row_persists_when_pass_two_differs_after_streaming_started`
   (real PostgreSQL, runtime role): one committed FAILURE row in a fresh session, actor and
   `ip == "testclient"`; the tampered last chunk is not in the response.
3. **LOW, done.** The generator closes the pass-2 stream in a `finally`
   (`test_pass_two_stream_is_closed_when_the_client_goes_away`). If the client goes away before the
   first chunk is requested the generator never starts and the stream is released by collection, as before.
4. **LOW, for the orchestrator.** TC-007.13 states that the SUCCESS-then-FAILURE sequence follows ADR-0021
   and that FAILURE is the final outcome. ADD-012 is approved and not edited here; its wording ("SUCCESS
   means verified and serving started; an aborted transfer adds a FAILURE row") goes to TASK-225.
   Finding 5 (two reads per download) goes to TASK-226 as QA noted.

Verification: `uv run pytest -q` 1580 passed, 10 skipped; `ruff check .` clean; `ruff format --check` clean
on `app` and `tests/attachments`; `mypy app` clean. `OBJECT_STORE_INTEGRATION=1` against a throwaway
`chrislusf/seaweedfs:4.51@sha256:f7a49e3f…` container (removed afterwards):
`test_object_store_conditional_read.py` and `test_object_store_sse.py`, 8 passed. Not run: mutation check of
the held-back chunk against the old code (the ASGI test's `len(body) <= 262144` bound fails for it by
construction: the old code sent all 300000 bytes).

## QA review round 2 (qa-engineer, 2026-11-13) — CHANGES REQUESTED

Run by QA: backend suite 1580 passed, 10 skipped, 0 failed; `ruff check`, `mypy app` clean; `ruff format`
clean on touched files; OpenAPI byte-identical; `traceability-check` (fallback, 78 records) 0 errors.
Round 1 findings 2 (real-DB FAILURE row), 3 (TC-007.13 wording) and 4 (`finally` close) are closed. Finding 1
is closed for a same-length tamper. Real uvicorn plus `curl`, stored size 300000: last byte flipped →
262144 bytes, curl exit 18; pass 2 of 400000 random bytes → 262144 bytes, exit 18; untouched → 300000 bytes,
exit 0. The real-server test `test_over_http_a_tampered_second_pass_is_a_failed_transfer_not_a_complete_200`
together with its untouched control is enough evidence that the transfer never completes; the ASGI-level
test does not need to assert it.

1. **[HIGH] A longer pass 2 still reaches the client as a complete 200 when the stored size is a multiple
   of 64 KiB.** `_verified()` checks `count != attachment.size` only after pass 2 is exhausted, so while
   the bytes stream it keeps yielding held chunks past the stored size. uvicorn refuses the chunk that would
   exceed `Content-Length`, but if the size falls on a chunk boundary, every declared byte has already
   gone out. QA probe: stored object 262144 bytes (4 × 64 KiB), pass 2 = 362144 random bytes → `http=200
   size=262144`, curl exit 0, body equal to the tampered prefix; the server logs "Response content longer
   than Content-Length". → Inside the loop, as soon as `count > attachment.size`, record FAILURE and
   raise before yielding anything more. Add a test case (stored size an exact multiple of 64 KiB, longer
   pass 2) to the uvicorn test and the ASGI test, and to TC-007.13.

## Round 3 (Software Developer, 2026-11-13)

**HIGH, fixed.** In `_verified()` (`backend/app/attachments/service.py`) the running byte count is now
checked as each chunk is read: the moment it would exceed `attachment.size`, FAILURE is recorded and
`AttachmentIntegrityError` is raised before the held chunk or anything further is yielded. Empty chunks
are skipped. The held chunk is released only when pass 2 has ended with `count == size` and the digest
matches. Why that is enough: before the final check the bytes sent are always `count` minus the held and
the current chunk, so they are strictly fewer than `size` whenever a chunk is non-empty, and
`Content-Length` can never be satisfied by an unverified response. Boundaries reasoned through: shorter
(count check at the end), same length but different (digest check at the end, last chunk held), longer
(guard on the running count, also when the stored size is an exact multiple of 64 KiB), stored size 0
(any byte trips the guard; an empty pass 2 verifies against the empty digest and sends nothing), a single
chunk (held until the end), exactly one full chunk (same).

Tests: `TAMPER_CASES` in `backend/tests/attachments/test_attachment_download.py` has 18 cases (shorter by
one byte, by whole chunks, empty; same length with the last or first byte changed; longer by a few bytes
and by whole chunks; stored multiple of 64 KiB: changed, shorter, longer with the same prefix, longer
random (QA's reproduction); single chunk: changed, longer, shorter; exactly one full chunk: changed,
longer; size 0 given data or a full chunk) and 5 untouched controls (including multiple of 64 KiB, single
chunk, one full chunk, size 0). Both
`test_client_never_receives_a_complete_response_when_pass_two_is_tampered` (ASGI: body shorter than
`Content-Length`, error raised, FAILURE row) and
`test_over_http_a_tampered_second_pass_is_a_failed_transfer_not_a_complete_200` (real uvicorn and
`httpx`: transport error, never a complete 200 with other content than the stored object) run over all 18;
the controls complete and equal the stored bytes. For size 0 the client gets the true, empty content
(`Content-Length: 0`), which is complete and carries no byte.

Note: a tampered *non-final* chunk (for instance a changed first byte) is still sent before the end of
pass 2 is known; the transfer is then aborted short of `Content-Length`. That is the accepted behaviour
of ADR-0021 (the client cannot take it as a complete file); only the unverified final chunk is withheld.

Mutation check: with the new guard disabled (`if False:`), 7 tests fail — the ASGI and the uvicorn case
for `longer_by_whole_chunks` (ASGI only), `multiple_of_chunk_longer_with_prefix`,
`multiple_of_chunk_longer_random` and `exactly_one_full_chunk_longer` — and the other 50 pass; guard
restored, 57 pass. Verification: `uv run pytest -q` 1622 passed, 10 skipped; `ruff check .` clean;
`ruff format --check` clean on `app` and `tests/attachments`; `mypy app` clean.

## QA review round 3 (qa-engineer, 2026-11-13) — APPROVED

Run by QA: backend suite 1622 passed, 10 skipped, 0 failed; `ruff check`, `mypy app` clean; `ruff format`
clean on touched files (the same 3 pre-existing files); OpenAPI byte-identical. Real uvicorn plus `curl`
against the working tree: stored 300000 → last byte flipped 262144 B exit 18, longer 196608 B exit 18,
untouched 300000 B exit 0; stored 262144 (4 × 64 KiB) → pass 2 of 362144 B 196608 B exit 18, last byte
flipped 196608 B exit 18, untouched 262144 B exit 0. With the stored size above 0, a tampered pass 2 never
satisfies `Content-Length`. A tampered non-final chunk can still reach the client before the abort, which
ADR-0021 accepts ("the client sees a broken download"). The real-store run of round 1 (8 passed, pinned
SeaweedFS 4.51, SSE-S3) still applies, because `object_storage.py` has not changed since. `traceability-check`
(fallback) on CR-006, TASK-217, TS-007, PRB-008, SOUP-036: 0 errors. All earlier findings are closed. Still
open, none of them blocking: SOUP-036 1.5 needs the human's approval; the audit-row semantics go in ADD-012
(TASK-225); TASK-226 measures the cost of the second read (SR-026 AC 3/AC 5). TS-007's 1.10 history lines
are now in date order. PRB-008 `investigating → resolved`.

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect) from the download half of
  TASK-135 1.2, with the D-10 binding and the SOUP-036 confirmation as its first step.
- 1.1 (2026-11-13) — Implemented (Software Developer). Step 1 passed on the pinned digest; implementation
  record added; SOUP-036 and SOUP-019 left unedited (approved). `draft → in_review`.
- 1.2 (2026-11-13) — QA review: CHANGES REQUESTED (1 HIGH, 1 MEDIUM, 3 LOW; see "QA review"; suite 1574 passed, 10 skipped, 0 failed); `in_review → draft`.
- 1.3 (2026-11-13) — Round 2 (Software Developer): findings 1–4 addressed (last chunk held back until the
  digest matches; client-side and real-DB tests; stream closed in `finally`; audit wording noted for
  TASK-225); see "Round 2". `draft → in_review`.
- 1.4 (2026-11-13) — QA review round 2: CHANGES REQUESTED (1 HIGH: a longer pass 2 completes the response when the size is a multiple of 64 KiB); `in_review → draft`.
- 1.5 (2026-11-13) — Round 3 (Software Developer): pass 2 is stopped the moment it would exceed the stored size; 18 tamper boundaries plus 5 controls at ASGI and real-uvicorn level; mutation check recorded; see "Round 3". `draft → in_review`.
- 1.6 (2026-11-13) — QA review round 3: APPROVED (see "QA review round 3"); checkboxes ticked; `in_review → approved`.
