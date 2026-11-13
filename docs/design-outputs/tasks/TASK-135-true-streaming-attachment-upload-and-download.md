---
id: "TASK-135"
type: task
title: "Bounded-memory attachment upload with the limit enforced while reading"
status: approved
version: "1.7"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-11-13"
links:
  - target: "SR-013"
    relation: implements
  - target: "SR-026"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-008"
    relation: relates_to
  - target: "PRB-078"
    relation: relates_to
  - target: "ADD-012"
    relation: relates_to
  - target: "TS-007"
    relation: relates_to
  - target: "SR-031"
    relation: relates_to
  - target: "NFR-008"
    relation: relates_to
  - target: "TASK-125"
    relation: relates_to
tags: ["phase:review-2026-07", "cr:CR-006", "remediation-of:TASK-125", "control:design"]
---

# TASK-135 — Bounded-memory attachment upload with the limit enforced while reading

- **Software item / unit:** SI-ATTACH `U-ATT-Upload` (ADD-012); SI-API attachment router (ADD-005);
  reverse proxy (ADD-026).
- **PRB:** PRB-008 (upload half; the download half is TASK-217). **CR:** CR-006 (D-2; ADR-0021).
- **Depends on:** none. First backend task of CR-006. TASK-136 step 1 (load-test baseline) runs before
  this task is committed.
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** M (`backend/app/api/routers/attachments.py`, `backend/app/attachments/service.py`,
  `backend/app/core/object_storage.py`, `backend/app/attachments/dicom_validation.py`,
  `infra/reverse-proxy/nginx.conf`; tests `backend/tests/attachments/`, `infra/tests/`; records TS-007,
  ADD-012, SOUP-003/017 relied-on text if it changes).

## Objective

SR-013 AC 6: an upload never holds the whole object in the API process, and an upload over the maximum is
refused with an RFC 7807 error after reading at most the maximum plus one chunk. Today
`upload_attachment` does `await file.read()` (`api/routers/attachments.py:62`) and
`AttachmentService.store` checks `len(data)` afterwards (`attachments/service.py:69-74`). The maximum is
raised from 100 MiB to 150 MiB (CR-006 D-2, SR-017 AC 6). Also restores SR-013 AC 1 on the deployed stack:
`infra/reverse-proxy/nginx.conf` sets no `client_max_body_size`, so nginx's 1 MiB default refuses every
larger upload before it reaches the application (found at the Plan stage, CR-006 finding P-4; PRB-078, D-18).

## Implementation detail (ADR-0021, upload)

- `attachment_max_bytes` default 157286400 (150 MiB) in `core/config.py`; the `getattr` fallback in
  `service.py:70` goes.
- **Early refusal:** for `POST /clinical-entries/{id}/attachments`, a pure-ASGI guard (mounted for that
  path only) refuses a `Content-Length` above `attachment_max_bytes + MULTIPART_ALLOWANCE` (64 KiB) and,
  for any body, counts `http.request` bytes and refuses once the count passes
  `attachment_max_bytes + 64 KiB` (the multipart allowance), so at most the maximum plus the 64 KiB
  allowance plus the one received message that crosses the bound is read. Same problem type and status as today's size refusal, so the
  OpenAPI contract does not change (export must stay byte-identical).
- **Handler:** keeps the `UploadFile` signature. `store()` takes the spooled file object instead of
  `bytes`: it reads 64 KiB chunks, counts and hashes (SHA-256) incrementally, refuses when the count passes
  the maximum, then `seek(0)`. Starlette spools a file part to disk beyond 1 MiB, so memory stays bounded.
- **DICOM validation** (`validate_dicom`) takes a file object: `dcmread(fp, stop_before_pixels=True)`,
  then `seek(0)`.
- **Object store:** `ObjectStorageClient.put_object(key, fileobj, size, content_type)` calls boto3
  `put_object(Body=fileobj, ContentLength=size, ServerSideEncryption="AES256")`: one `PutObject`, never
  `upload_fileobj` (SOUP-019, SOUP-036 issue #8908).
- The blocking `svc.store(...)` is called through `run_in_threadpool` (TASK-136 owns the static check).
- **Reverse proxy:** `client_max_body_size 151m;` (maximum plus allowance, rounded up) in the
  `location /api/` block; an `infra/tests` check that it is present and not smaller than
  `attachment_max_bytes`.
- Unchanged: the file-name bound (TASK-206), SSE, the rollback of the object on a DB failure, the audit row.

## Tests (write first)

- `test_upload_over_limit_refused_within_limit_plus_one_chunk` (SR-013 AC 6): a body of max + 10 MiB sent
  as a generator; assert the problem response and that the bytes pulled from the generator are
  ≤ max + 64 KiB + allowance. Run with a small `attachment_max_bytes` override (for example 1 MiB).
- `test_upload_content_length_over_limit_refused_before_body` (SR-013 AC 6).
- `test_upload_memory_bounded` (SR-013 AC 6): `tracemalloc` peak during a 20 MiB upload stays below a
  fixed bound (for example 4 MiB) independent of size (two sizes, same bound).
- `test_upload_at_limit_accepted` (SR-013 AC 6, SR-017 AC 6): an object of exactly the maximum is stored;
  the stored checksum equals the SHA-256 of the input; `put_object` called once with a file body.
- `test_dicom_validation_reads_header_from_file` (SR-013 AC 1); existing DICOM and modality tests unchanged.
- `infra/tests`: nginx `client_max_body_size` present and ≥ maximum.
- Recorded in TS-007 (first CR-006 task to change it: 1.8 → 1.9, approval cleared), new TC-007.9.

## Acceptance criteria

- [x] SR-013 AC 6 (upload): over-limit refused with an RFC 7807 error after at most max + one chunk; memory
  bounded independently of object size.
- [x] Maximum is 150 MiB (D-2); an object of exactly 150 MiB is accepted.
- [x] Deployed stack accepts an upload above 1 MiB through nginx (SR-013 AC 1).
- [x] OpenAPI export byte-identical; existing attachment and DICOM tests pass.

## Definition of Done

- [x] `ruff`, `mypy`, backend suite and `infra/tests` green
- [x] TS-007 updated; ADD-012 consistent (already describes the planned unit, CR-006 Plan)
- [x] `traceability-check` shows no error for this record

## Implementation record (software-developer, 2026-11-13)

Changed: `backend/app/core/config.py` (`attachment_max_bytes` = 157286400); `backend/app/core/body_limit.py`
(new pure-ASGI guard, mounted innermost in `app/main.py`, upload route and POST only; its refusal is built
from `ValidationProblem`, so status, type and body shape are today's 400 `validation-error`; the over-count
is raised out of `receive` as a `BaseException` subclass because FastAPI's `except Exception` around form
parsing would turn an ordinary exception into a generic 400); `backend/app/api/routers/attachments.py`
(no `await file.read()`; `run_in_threadpool(svc.store, ..., file.file)`); `backend/app/attachments/service.py`
(`store()` takes the file object, 64 KiB chunks, incremental SHA-256, refusal once the count passes the
maximum, `seek(0)`, the `getattr` fallback removed); `backend/app/attachments/dicom_validation.py`
(`dcmread(fp, stop_before_pixels=True)` then `seek(0)`); `backend/app/core/object_storage.py`
(`put_object(key, fileobj, size, content_type)`, one `PutObject`, `ContentLength` set, no `upload_fileobj`);
`infra/reverse-proxy/nginx.conf` (`client_max_body_size 151m;` in `location /api/`); `infra/docker-compose.yml`
and `infra/.env.example` (`ATTACHMENT_MAX_BYTES`, default 157286400, needed because
`infra/tests/test_compose_settings_coverage.py` and `backend/tests/test_env_example.py` require every
`Settings` field to be wired and documented).

Tests: `backend/tests/attachments/test_attachment_upload.py` (existing calls now pass `io.BytesIO`; new
`test_upload_over_limit_refused_within_limit_plus_one_chunk`, `test_upload_one_byte_over_limit_refused`,
`test_upload_at_limit_accepted`, `test_upload_memory_bounded`), `backend/tests/attachments/test_dicom_validation.py`
(`test_dicom_validation_reads_header_from_file`), `backend/tests/core/test_attachment_body_limit.py` (new:
over-limit stream, `Content-Length` over the bound refused before the body, at-the-bound passes, other
routes untouched, two through-the-app tests), `infra/tests/test_proxy_body_limit.py` (new),
`backend/tests/integration/test_object_store_sse.py` (call signature only; skipped without a store).
TS-007 1.9 TC-007.12 (numbered .12 because CR-004 already issued .9 to .11).

Deviations from the task text, for QA: (1) `test_upload_over_limit_refused_...` and
`test_upload_content_length_over_limit_refused_before_body` drive the guard at ASGI level, because
Starlette's `TestClient` delivers the whole body as one message, so "bytes pulled from a generator" cannot
be observed through it; (2) the memory test measures the service with a chunk-producing file object (the
Starlette spooling is exercised by the through-the-app test, not by tracemalloc); (3) the guard answers
the over-limit stream case before authentication (it runs first), the same status and body as the
service's refusal; (4) `ATTACHMENT_MAX_BYTES` wiring added (see above).

Verification run: `uv run pytest -q` in `backend/`: 1303 passed, 6 skipped, 257 errors, 0 failed. All 257
errors are `docker.errors.DockerException` (testcontainers cannot reach the Docker daemon from this
sandbox; the real-DB tests, among them `test_attachment_integrity_persistence.py`, did not run). `ruff
check`, `ruff format --check` on the touched paths, `mypy app`: clean. `python3 -m unittest discover -s
infra/tests`: 177 tests OK. OpenAPI export diffed against `backend/openapi/openapi.json`: identical.
nginx: real nginx 1.31.8-alpine, committed configuration versus working tree, bodies of 2 MB, 100 MB,
150 MiB and 160 MB: HEAD 413 for all, working tree 200, 200, 200, 413. boto3 `Stubber` accepts a
`SpooledTemporaryFile` body with `ContentLength`. Not verified: a real upload through the started stack to
the real object store (the stack running on this machine was not rebuilt); the real-DB tests above.

Findings outside the task: RISK-007's CR-006 control row (line 83, "none yet (planned: ...)") should name
TC-007.12 as its verification once the human re-approves RISK-007; I did not edit it. `Settings` had no
`attachment_max_bytes` field at all (the service used a `getattr` fallback), so the 100 MiB default
documented in PRB-078 was never configurable.

## QA review (qa-engineer, 2026-11-13) — CHANGES REQUESTED

Verification run by QA: backend `uv run pytest -q` 1560 passed, 6 skipped, 0 failed, 0 errors (run twice:
`DOCKER_API_VERSION=1.43` outside the sandbox, then plainly after the Docker restart; real-DB tests ran);
`ruff check` clean; `ruff format --check` clean on every touched file (3 untouched files pre-existing:
`tests/api/test_openapi_contract.py`, `tests/auth/test_session_service.py`, `tests/test_env_example.py`);
`mypy app` clean; `infra/tests` 177 OK; OpenAPI export byte-identical. Extra probes: (a) through the real
app with a chunked multipart body and no `Content-Length` (5 MiB, maximum 1 MiB): 400 `validation-error`
problem, service not called, bytes pulled = bound + 104, same for an unauthenticated caller; (b) pinned
SeaweedFS 4.51 image, `ObjectStorageClient.put_object` with a rolled-over `SpooledTemporaryFile` of 3 MiB and
150 MiB: stored length equal, `ServerSideEncryption: AES256`, SHA-256 of the read-back equal, peak Python
allocation 2.4 MiB. `traceability-check` (fallback procedure) on CR-006, TASK-135, TS-007, PRB-008, PRB-078
and their neighbours (74 records): 0 errors; warnings W1 SR-017, SR-026 (TS-019/TS-018 planned), W5 TASK-204,
TASK-206, TP-001 → TS-007 `in_review` (clears when TS-007 is approved).

Findings (fix before re-review):

1. **[HIGH] The Starlette spooling that the memory bound rests on is neither recorded nor tested.** ADR-0021
   ("bounded by the chunk size and Starlette's 1 MiB spool threshold") and the CR-006 Plan SOUP table
   ("SOUP-003 … relied-on text extended by TASK-135 (spooled `UploadFile`)") assign it to this task;
   `docs/soup/SOUP-003-starlette.md` is unchanged (1.2, "Functional and performance requirements" names only
   the middleware chain), and `test_upload_memory_bounded` deliberately bypasses Starlette (deviation 2), so no
   test shows the file handed to `store()` is on disk. → Add to SOUP-003 the relied-on behaviour (multipart
   file parts are `UploadFile` over `SpooledTemporaryFile(max_size=1 MiB)`, `starlette/formparsers.py`
   `spool_max_size`; the 1 MiB `max_part_size` for non-file fields), version 1.3, approval cleared,
   `in_review`; and add a through-the-app test (in `backend/tests/core/test_attachment_body_limit.py`) that
   uploads > 1 MiB and asserts the object passed to `svc.store` is a rolled-over spooled file
   (`fileobj._rolled` or `fileobj.fileno()` succeeds), referenced from TC-007.12.
2. **[MEDIUM] The counting path is not tested through the full app.** Both through-the-app tests use
   `TestClient`, which sends `Content-Length`, so only the header refusal runs inside FastAPI; the
   `_BodyTooLarge`-out-of-`receive` path (the one that relies on FastAPI's `except Exception` not catching a
   `BaseException`) is only tested against a stub app. QA probe (a) shows it works today. → Add a
   `create_app()` test driven at ASGI level with a chunked multipart body and no `Content-Length` (as in
   `_run`), asserting the 400 problem, `pulled <= MAX + MULTIPART_ALLOWANCE + CHUNK` and `store` not called.
3. **[MEDIUM] TS-007 TC-007.12 claims SR-017 AC 6 and SR-026 AC 5, which TS-007 does not verify.**
   `TS-007` links `verifies` SR-012, SR-013, SR-023 only and its Scope says the same; CR-006 Plan gives SR-017
   to TS-019 (TASK-218) and SR-026 to TS-018 (TASK-136). → In the Verifies column keep "SR-013 (AC 1, AC 6)"
   and move the other two into the expected-result text as context ("the SR-013 maximum equals the SR-017
   AC 6 stored bound; contributes to SR-026 AC 5, verified in TS-018"), or add the links and Scope lines.
4. **[MEDIUM, human decision] Above 151 MiB the deployed stack refuses with nginx's 413 page, not an RFC 7807
   error** (SR-013 AC 6 "refused with an RFC 7807 error"; PRB-078 Impact already notes the page is not a
   problem document; no `error_page 413` in `infra/reverse-proxy/nginx.conf`, and the frontend has no size
   pre-check). Between 150 MiB + 64 KiB and 151 MiB the API answers the problem. Not caused by this task, and
   any finite proxy limit has the same edge. → Human: accept as a known anomaly (as TASK-207 finding 5 accepted
   the 2 MB 413) and record it in PRB-078/TC-007.12, or plan an nginx `error_page 413` returning an
   `application/problem+json` body (status 413) or a client-side size check in TASK-143. Does not block this
   task once decided.
5. **[LOW] Before-authentication refusal: accepted, no human decision needed.** ADR-0021 places the refusal
   before the form is parsed, and FastAPI parses the body before `get_current_user`, so this follows from the
   approved design. The CSRF middleware still runs first; the answer is the same for every entry id (no
   existence oracle) and discloses only the configured maximum; it stops unauthenticated callers from filling
   the spool directory. → TASK-225: state in ADD-012 `U-ATT-Upload` that the guard answers before
   authentication.
6. **[LOW] Bytes read past the maximum.** The guard reads at most maximum + 64 KiB allowance + the last
   receive message (probe: +104 bytes), and the test allows maximum + two chunks, as the task text and ADR-0021
   specify; SR-013 AC 6's "plus one chunk" is met only if the allowance is read as framing. → TASK-225/TS-007:
   say "maximum plus the 64 KiB multipart allowance plus one received chunk" consistently.
7. **[LOW] `ATTACHMENT_MAX_BYTES` wiring.** Confirmed required (`infra/tests/test_compose_settings_coverage.py`
   has an empty `EXCEPTIONS`; `backend/tests/test_env_example.py::test_env_example_covers_all_settings_fields`).
   Default equals the code default, so it changes no deployed behaviour beyond the approved D-2 value; it is
   not one of the Plan's "ask first" values (pool and thread sizes, D-14/D-17). ADD-026 `U-DEP-Compose` does
   not list it. → TASK-225: add it to ADD-026 and `infra/DEPLOY.md`.

For the orchestrator (records QA does not edit): RISK-007 line 83 verification cell → "TS-007 TC-007.12
(upload)" at its next revision. TASK-136 step 1 baseline: nothing in TASK-135 prevents it; HEAD, `main` and
`origin/main` are all `8028685` (pre-CR-006), so take it from a worktree pinned to `8028685`; uploads above
1 MiB there must bypass nginx (PRB-078). The CR-006 Plan-stage records (CR-006, ADR-0021, PRB-078, TASK-217…226
and the modified SR/ADD/RISK/SOUP files) are uncommitted on the branch; commit them before this task's commit.

## Round 2 (software-developer, 2026-11-13)

1. HIGH. (b) Done: `test_upload_above_one_mib_reaches_the_service_as_a_file_already_on_disk`
   (`backend/tests/core/test_attachment_body_limit.py`, real multipart through `create_app()`, asserts
   the file seen by `store()` has `_rolled` true), in TC-007.12. (a) PARTLY DONE and BLOCKED: the
   relied-on text (spooling via `MultiPartParser.spool_max_size` 1 MiB, `max_part_size` for non-file
   fields, version-specific, TMPDIR sizing) is written into the body of
   `docs/soup/SOUP-003-starlette.md`; the edit of its frontmatter (`approved` → `in_review`, version 1.3,
   removal of `approved_by`, `approved_on`, `approved_digest`, `approval_note`) and of its change log
   was refused by the permission system, so SOUP-003 is at present approved with a body that no longer
   matches its digest. Those three edits are still to be made (by the human or after a permission is
   granted).
2. MEDIUM. Done: `test_chunked_over_limit_upload_through_the_full_app_is_refused_by_the_count` drives
   `create_app()` at ASGI level with a chunked multipart body and no `Content-Length`: 400
   `validation-error` problem, bytes pulled within the bound, service never called.
3. MEDIUM. Done: TC-007.12 `Verifies` is SR-013 (AC 1, AC 6); SR-017 AC 6 and SR-026 AC 5 are context
   text only; no links added.
4. MEDIUM (nginx 413 page above 151 MiB): human decision "error_page en nginx", done.
   `location /api/` has `error_page 413 =400 @upload_too_large;`; the internal named location returns
   `application/problem+json`, status 400, type `.../errors/validation-error`, title `Validation Error`,
   fixed detail, `errors: []`, without `instance` or upstream detail, plus the server-level security
   headers. Status 400 (not 413) to match the API's own refusal of the same condition, so the client
   sees one contract; SR-013 AC 6 asks only for an RFC 7807 error. `proxy_intercept_errors` stays off so
   upstream answers are untouched. `infra/tests/test_proxy_body_limit.py` checks the directive, the body
   and the absence of upstream detail (178 infra tests OK); real nginx: 2 MB and 150 MiB reach the
   upstream, 160 MB gives 400 with `Content-Type: application/problem+json`. SOUP-024 (nginx, approved
   1.5) does not mention body limits or error pages; not edited, no relied-on text needs it (the
   behaviour is documented nginx `error_page`/`client_max_body_size`).
5. LOW 6. Done: "maximum plus the 64 KiB multipart allowance plus one received chunk" in
   `backend/app/core/body_limit.py`, this record's implementation detail and TS-007 TC-007.12.
   PRB-078's Resolution now holds the reproduction commands. Findings 5 and 7 are TASK-225's.

## QA review round 2 (qa-engineer, 2026-11-13) — APPROVED

Run by QA: backend `uv run pytest -q` (plain, Docker normal) 1562 passed, 6 skipped, 0 failed; `ruff check`
clean, `ruff format --check` clean on touched files (the same 3 pre-existing files); `mypy app` clean;
`infra/tests` 178 OK; OpenAPI export byte-identical. Real nginx 1.31.8-alpine with the working-tree
`nginx.conf` (PRB-078 procedure, own names and port 18445): 2 MB and 150 MiB → 200 from the stub upstream;
160 MB → 400, `application/problem+json`, the fixed validation-error body, and exactly the server-level
headers (`Strict-Transport-Security: max-age=31536000; includeSubDomains`, `X-Content-Type-Options: nosniff`,
`X-Frame-Options: DENY`; the server block sets no others). `traceability-check` (fallback) on CR-006,
TASK-135, TS-007, PRB-008, PRB-078, SOUP-003 and their neighbours (80 records): 0 errors; warnings W1
SR-017/SR-026 (planned TS-019/TS-018), W5 approved records → TS-007/SOUP-003 `in_review` (clear on approval).
Findings 1–3 and 6 closed; 4 closed by the human's `error_page` decision; 5, 7 stay with TASK-225.

Non-blocking:
- **[MEDIUM] SOUP-024 does not list the nginx directives now relied on.** Its relied-on text lists the
  directives MedHub depends on (`map`, `~*`, `escape=json`, `add_header` replacement) but not
  `client_max_body_size` (SR-013 AC 1) or `error_page 413 =400` to an internal named location with
  `return` (SR-013 AC 6); the CR-006 Plan's "relied on as recorded (`client_max_body_size`)" is not what
  the record says. → Add one sentence to SOUP-024 citing `infra/tests/test_proxy_body_limit.py` and the
  PRB-078 run (human re-approval), before CR-006 closes (TASK-225 is fine).
- **[LOW] The 413 mapping covers every `/api/` route,** so a > 151 MiB body to any other API route gets
  "The attachment exceeds the maximum size." Harmless; reword the detail if it matters.

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-003 (risk register bootstrap, TASK-147).
- 1.2 (2026-10-21) — Tagged `control:protective` (medical-records 0.3.2).
- 1.3 (2026-11-13) — CR-006 Plan stage (Software Architect). Narrowed to the upload half of PRB-008; the
  download half moves to TASK-217 (bound two-pass read, D-6, D-10). Re-based on SR-013 AC 6 and the 150 MiB
  maximum (D-2); nginx body limit added (finding P-4). `mitigates` RISK-003 removed: RISK-003 1.2 corrected
  its row (the DICOM bound is TASK-218, not this task); `mitigates` RISK-007 added (bounded attachment IO
  row). Implements SR-026 (AC 5: no request exhausts the worker). Same day, after the Plan gate: `relates_to`
  PRB-078 (the nginx limit, D-18). Still `draft`.
- 1.4 (2026-11-13) — Implemented (software-developer); implementation record added; `draft → in_review`.
  Checkboxes left for QA.
- 1.5 (2026-11-13) — QA review: CHANGES REQUESTED (1 HIGH, 3 MEDIUM, 3 LOW; see "QA review");
  `in_review → draft`.
- 1.6 (2026-11-13) — Round 2 (software-developer): findings 1 (test part), 2, 3, 6 addressed, SOUP-003
  update blocked (see "Round 2"); `draft → in_review`.
- 1.7 (2026-11-13) — QA review round 2: APPROVED (see "QA review round 2"); checkboxes ticked;
  `in_review → approved`.
