# ADR-0021: Attachment content is handled in bounded chunks, and the download is a bound two-pass read

## Status

Accepted (2026-11-13, Carlos Santiago Liceras, CR-006 plan gate). Proposed the same day at the
CR-006 Plan stage by the Software Architect role.

## Context

SR-013 AC 6 (CR-006) requires that upload and download never hold the whole object in the API
process and that an over-limit upload is refused after reading at most the limit plus one chunk.
SR-013 AC 5 requires that the SHA-256 of the content is verified **before** any byte is served.
Today (PRB-008) the upload does `await file.read()` and checks `len(data)` afterwards, and the
download reads the whole object into `bytes`, hashes it and re-chunks it from memory.

The two requirements pull in opposite directions for the download: a true stream sends bytes as
they are read, but AC 5 forbids serving unverified bytes. CR-006 D-6 chose two passes; D-10 (R-1)
requires the second read to be bound to the first so the bytes served are the bytes verified
(RISK-012). D-2 raises the attachment maximum to 150 MiB (SR-017 AC 6).

Also found at the Plan stage: `infra/reverse-proxy/nginx.conf` sets no `client_max_body_size`, so
nginx's default of 1 MiB refuses every larger upload on the deployed stack before it reaches the
application.

## Options

Upload:

1. **Read the `UploadFile` in chunks inside the handler** and keep Starlette's form parsing
   (python-multipart spools the file part to a temporary file beyond 1 MiB), with an early refusal
   from `Content-Length` and a byte-counting guard on the request body for the upload route.
2. **Replace Starlette's form parsing** with a streaming multipart parser in the handler
   (`request.stream()` into python-multipart's parser directly), changing the route signature.
3. **Stream straight to the object store** (S3 multipart upload) as the body arrives.

Download:

A. **Two passes, the second bound by `If-Match` on the ETag from the first, and hashed while
   sending** (D-6, D-10).
B. Two passes without binding (D-6 only): the object can be replaced between the passes.
C. One pass, hash while sending, abort on mismatch: unverified bytes reach the client (breaks
   SR-013 AC 5 as written).
D. Copy the object to a local temporary file, hash it, serve the file: bounded memory, one store
   read, but a 150 MiB temporary file per concurrent download on the API host.

## Decision

Upload: **option 1.** Download: **option A.**

- **Upload.** The route keeps its `UploadFile` signature, so the OpenAPI contract does not change.
  Before the form is parsed, a request whose `Content-Length` exceeds the maximum plus a fixed
  multipart allowance is refused; for the upload route a pure-ASGI body guard counts the bytes
  received and refuses once the maximum plus one chunk is passed, whatever the headers say. The
  handler reads the spooled file in 64 KiB chunks, counting and hashing incrementally; it refuses
  when the count passes the maximum. DICOM validation reads the header from the spooled file
  (`dcmread(..., stop_before_pixels=True)`). The object is sent with one `PutObject` whose body is
  the spooled file (`ContentLength` set), never a multipart upload (SOUP-036 relies on single
  `PutObject` only; issue #8908). The refusal keeps today's problem type and status. The maximum is
  150 MiB (`attachment_max_bytes`, D-2). nginx gets `client_max_body_size` equal to the maximum plus
  the multipart allowance, as defence in depth.
- **Download.** `AttachmentService.open_stream()`: pass 1 `GetObject`, hash with
  `iter_chunks(64 KiB)` keeping nothing, remember the `ETag`; compare with the stored checksum
  (constant time). On a match, pass 2 `GetObject(IfMatch=etag)` **before** the response starts, so a
  412 (object replaced) becomes the SR-013 AC 5 answer (502 problem, FAILURE audit row on its own
  transaction, ADR-0016). The response body is a generator over pass 2 that hashes as it sends; on a
  mismatch at the end it records a FAILURE row and raises, so the server aborts the connection
  without completing the chunked body and the client never sees a complete response. The SUCCESS
  `ATTACHMENT_ACCESS` row is written when pass 2 has been opened (as today: after verification,
  before serving).
- **Module path.** `open(actor, id, max_bytes=None)` stays (bytes, verified before return) for the
  DICOM module, which must decode a whole object anyway; with `max_bytes` it refuses from
  `attachment.size` before reading (SR-017 AC 6, TASK-218).

Option 2 was rejected: it changes the route signature and the OpenAPI document (an "ask first"
contract change) for no gain over option 1, whose memory is already bounded by Starlette's spooling.
Option 3 was rejected: it needs S3 multipart uploads, which SOUP-036 does not rely on and which issue
#8908 makes suspect, and it cannot validate DICOM before writing. Option B leaves the substitution
path of RISK-012 open (residual 4 × 2 → alarp). Option C breaks SR-013 AC 5. Option D moves the
memory problem to the disk of the API host and adds a clean-up path for no requirement.

## Consequences

### Positive

- Memory per upload and download is bounded by the chunk size and Starlette's 1 MiB spool
  threshold, independent of the object size (SR-013 AC 6, RISK-007).
- The bytes served are the bytes verified (SR-013 AC 5 unchanged, RISK-012 stays 4 × 1).
- No HTTP contract change, no new dependency.

### Negative

- Two object-store reads per download: a 150 MiB study is read twice (SR-026 AC 3 measured in the
  CR-006 load test, TASK-226).
- An upload is written once to a temporary file on the API host before it is sent (disk, not
  memory); the temporary directory must hold the concurrent uploads (20 × 150 MiB at worst).
- A mismatch found in the second pass aborts a transfer already under way; the client sees a broken
  download, not a problem document. That only happens if the store changes the object between its
  own precondition check and its read, or corrupts it in transit.
- The binding relies on SeaweedFS's `If-Match` (SOUP-036 behaviour 14), confirmed from the published
  source and to be confirmed by a run (TASK-217 step 1); if the run fails, the D-10 fallback applies.

### Neutral

- The reverse-proxy limit is a deployment setting (ADD-026) and must follow `attachment_max_bytes`.

## References

- Requirements: SR-013 AC 5, AC 6; SR-017 AC 6; SR-026 AC 3, AC 5; SR-023 AC 2
- Problem reports: PRB-008 (and the nginx 1 MiB default, found at the Plan stage)
- Risks: RISK-007, RISK-012
- SOUP: SOUP-003 (Starlette), SOUP-017 (python-multipart), SOUP-019 (boto3), SOUP-036 (SeaweedFS), SOUP-024 (nginx)
- Related: ADR-0009, ADR-0015, ADR-0016; ADD-012, ADD-026; CR-006 D-2, D-6, D-10
