---
id: "TASK-232"
type: task
title: "Answer a logged 503 problem when the upload body cannot be spooled to disk"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-16"
updated: "2026-11-16"
links:
  - target: "SR-013"
    relation: implements
  - target: "SR-027"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-007"
    relation: relates_to
  - target: "PRB-092"
    relation: relates_to
  - target: "TASK-231"
    relation: relates_to
  - target: "ADD-005"
    relation: relates_to
  - target: "ADD-012"
    relation: relates_to
  - target: "TS-007"
    relation: relates_to
  - target: "TS-011"
    relation: relates_to
  - target: "SOUP-002"
    relation: relates_to
  - target: "SOUP-003"
    relation: relates_to
tags: ["cr:CR-007", "control:protective", "backend", "api-contract"]
---

# TASK-232 — Answer a logged 503 problem when the upload body cannot be spooled to disk

- **Software items / units:** SI-API attachments router (`backend/app/api/routers/attachments.py`, ADD-005)
  and `U-API-ErrorHandler` (`backend/app/api/errors.py`, ADD-005); the upload path of SI-ATTACH
  (`U-ATT-Upload`, ADD-012) is unchanged. SI-FE-APICLIENT and `AttachmentUpload` get tests only.
- **PRB:** PRB-092. **CR:** CR-007 (D-7, human decision 2026-11-16: "Add a code fix in CR-007").
- **Depends on:** none. **Before:** TASK-231 round 2, which records the behaviour this task builds.
- **Branch:** `fix/cr-007-review-followups`.
- **Size:** M (`errors.py`, `attachments.py`, `backend/tests/api/test_attachments_router.py`,
  `frontend/src/api/client.test.ts`, `frontend/src/core/clinical/AttachmentUpload.test.tsx`; the generated
  `backend/openapi/openapi.json` and `frontend/src/api/generated/openapi.ts`; records).

## Objective

When the API container's upload scratch directory is full (or the spool write fails for any other OS
reason), Starlette's `SpooledTemporaryFile` raises `OSError` inside `await request.form()`. FastAPI 0.138.0
(`fastapi/routing.py:420-465`) turns any non-`HTTPException` error there into
`starlette.exceptions.HTTPException(400, "There was an error parsing the body")` raised `from` the original
error. Today the user gets a plain-JSON 400 that reads as their own fault, the API logs nothing, and the
generic 500 handler (`errors.py:206-221`) never runs (TASK-231 QA R1-1).

After this task the same failure is:

- **logged** at `ERROR` by `app.api.routers.attachments`, with the method, the matched route template (as the
  500 handler does, SR-043 AC 4), the errno name and its text, and the traceback of the `OSError`; never the
  raw path, the upload's file name or any form field;
- **answered** `503 Service Unavailable`, `application/problem+json`, type
  `https://medhub.example/errors/upload-storage-unavailable`, `Retry-After: 30`, detail
  "The server could not receive the file because its temporary storage is unavailable. Nothing was saved;
  please try again later.";
- **stored nowhere**: the handler body, `AttachmentService.store`, the object store and the database are not
  reached (unchanged; the parse precedes the handler).

A genuinely malformed multipart body keeps today's 400 unchanged.

## Design

### Options considered

| Option | What | Verdict |
|---|---|---|
| A. Route class on the attachments router | `APIRoute` subclass whose `get_route_handler()` wraps FastAPI's handler and maps only a 400 `HTTPException` whose `__cause__` is an `OSError` to a new `ProblemError` | **Chosen** |
| B. App-wide `HTTPException` handler | Register a handler for Starlette's `HTTPException` in `register_error_handlers` that checks `__cause__` and delegates everything else to FastAPI's default handler | Same mechanism, but it replaces the default handling of every `HTTPException` (404, 405, every route) to serve one route |
| C. Custom `Request.form()` | Catch `OSError` in a `Request` subclass | A `ProblemError` raised there is caught by FastAPI's `except Exception` and becomes the same 400; it would need an `HTTPException` (plain JSON, not problem+json) or a `BaseException` trick like `_BodyTooLarge` |
| D. Parse the multipart in the route from `Request` | Drop `file: UploadFile`, call `request.form()` in the handler | Loses the generated `multipart/form-data` request body in the OpenAPI document (or needs hand-written `openapi_extra`), and moves validation out of FastAPI |
| E. Dependency | Parse in a dependency | Not possible: FastAPI reads the body before it solves dependencies |

Why A: it is FastAPI's documented extension point (custom `APIRoute` class), it touches one router, it
changes nothing for any other route or for any other error, and it does not alter the generated contract.
It gives up independence from a FastAPI internal: the mapping relies on FastAPI raising the 400 `from` the
original error. That reliance is recorded in SOUP-002 and pinned by the test of step 1, which runs against
the locked FastAPI and fails if a future version stops chaining (the 503 test then gets 400). Probe on the
locked versions (FastAPI 0.138.0, Starlette 1.3.1; scratch script, not in the repository): with
`tempfile.SpooledTemporaryFile.rollover` raising `OSError(ENOSPC)` the wrapper sees
`starlette.exceptions.HTTPException` (status 400, `__cause__` `OSError`); an 8 KB part header gives cause
`python_multipart.exceptions.MultipartParseError`; a missing boundary gives no cause (detail "Missing
boundary in multipart."). Note: catch `starlette.exceptions.HTTPException`, not `fastapi.HTTPException`
(a subclass that does not match).

### Status code: 503, not 507

- 503 is the project's code for a temporary server-side condition the client should retry: the catalogue
  already has `session-cap-contention` (`Retry-After: 1`) and `erasure-notification-unavailable`
  (`Retry-After: 30`), both `503` problems documented in the OpenAPI `responses`.
- The condition is temporary: the scratch space frees as concurrent uploads end (a 150 MiB upload took
  about 8.5 s through the proxy, TC-007.16), so "retry later" is the right instruction. `Retry-After: 30`
  matches the existing erasure value.
- 507 Insufficient Storage is WebDAV (RFC 4918 §11.5), means the resource itself cannot be stored, is not
  used anywhere in the project, and is wrong for the other `OSError`s mapped here (`EIO`, `EROFS`, `EMFILE`).

### Scope of routes

Multipart routes in the code base (`grep -rn "UploadFile\|Form(\|request.form" backend/app backend/modules`):
one, `POST /api/v1/clinical-entries/{entry_id}/attachments`. The DICOM module's routes take no body. The
route class is set on the attachments router (`APIRouter(tags=["attachments"], route_class=...)`); its other
routes read no body, so it changes nothing for them. A future multipart route elsewhere does not get the
mapping automatically; this is deliberate (no speculative scope).

### OpenAPI impact

Additive. The upload operation documents the new response as the download operation documents its 502:
`responses={503: {"description": ..., "content": {"application/problem+json": {"schema": {"$ref":
"#/components/schemas/ProblemDetail"}}}}}`. No schema, parameter or request body changes;
`frontend/src/api/generated/types.ts` is unchanged. Per CLAUDE.md: regenerate `backend/openapi/openapi.json`
and `frontend/src/api/generated/openapi.ts` and commit both.

### Frontend

No code change. `ApiClient.request` already turns any non-OK `application/problem+json` answer into
`ApiError(problem)` (`frontend/src/api/client.ts:67-76`; existing test "parses application/problem+json 5xx
into ApiError"), and `AttachmentUpload` shows `problem.detail` (`AttachmentUpload.tsx:27-33`). Tests prove
the 503 path end to end in the client.

## Steps

Test first: steps 1 and 2 are written and run against `HEAD` before any production change; step 1's first
test must fail (it gets 400), the others pass on `HEAD` and guard the unchanged behaviour.

1. **Backend tests**, `backend/tests/api/test_attachments_router.py`, new class `TestUploadScratchSpaceFailure`,
   through `create_app()` with the existing auth and service overrides of the file and a 2 MiB file part (above
   the 1 MiB spool threshold); `monkeypatch` `tempfile.SpooledTemporaryFile.rollover` to raise
   `OSError(errno.ENOSPC, os.strerror(errno.ENOSPC))`:
   - `test_spool_failure_answers_503_problem_and_stores_nothing`: status 503; `Content-Type`
     `application/problem+json`; body `type` ends with `/errors/upload-storage-unavailable`, `status` 503,
     `title` "Service Unavailable", the detail above; `Retry-After: 30`; the service's `store` is never called.
   - `test_spool_failure_is_logged_at_error_without_the_path_or_file_name` (`caplog`): exactly one `ERROR`
     record from `app.api.routers.attachments` that contains `ENOSPC` and the route template
     `/clinical-entries/{entry_id}/attachments`, carries `exc_info` of the `OSError`, and does not contain
     the entry UUID of the request or the upload's file name (use a name such as
     `jane.doe@example.com-scan.dcm`).
   - `test_malformed_multipart_still_answers_400` (parametrised): an 8 KB part header (as TC-007.11) and a
     `multipart/form-data` content type with no boundary each answer 400 exactly as on `HEAD`
     (`application/json`, detail unchanged), no `ERROR` record from the router logger, `store` not called.
   - `test_other_os_errors_in_the_handler_still_reach_the_500_handler`: `store` raising `OSError` gives the
     existing 500 `internal-error` problem (the mapping covers the body parse only).
2. **Frontend tests:** `frontend/src/api/client.test.ts`, in "ApiClient uploadAttachment": "surfaces the
   server detail of a problem+json 503" (`ApiError`, `problem.status` 503, `problem.detail` kept);
   `frontend/src/core/clinical/AttachmentUpload.test.tsx`: "shows the server's detail when the server cannot
   receive the file (503)".
3. **`backend/app/api/errors.py`:** `UploadStorageUnavailableProblem(ProblemError)`: status 503, title
   "Service Unavailable", `type_slug` `upload-storage-unavailable`, `headers = {"Retry-After": "30"}`, the
   detail above as default. Same shape as `ErasureNotificationUnavailableProblem`.
4. **`backend/app/api/routers/attachments.py`:** a private `APIRoute` subclass whose `get_route_handler()`
   wraps the handler from `super()`: on `starlette.exceptions.HTTPException` with `status_code == 400` and an
   `OSError` `__cause__`, log as in the Objective (module `logger`; route template read as
   `generic_error_handler` reads it; `errno.errorcode.get(err.errno, "unknown")` and `err.strerror`;
   `exc_info=err`) and raise `UploadStorageUnavailableProblem()` from the `OSError`; re-raise everything else
   unchanged. Set it as the router's `route_class`. Add the 503 entry to the upload route's `responses`.
   Nothing else in the router changes.
5. **Contract:** `cd backend && uv run python -m app.export_openapi --output openapi/openapi.json`;
   `cd frontend && npm run generate:types`; fix any TypeScript error (none expected).
6. **Records** (records only, same commit):
   - **TS-007** (approved 1.12 → 1.13, `in_review`, remove `approved_by`, `approved_on`, `approved_digest`,
     `approval_note`): new **TC-007.17** — Verifies SR-013 (AC 1), SR-027 (AC 3); the four tests of step 1;
     expected and pass criteria as written there; "Fails on `HEAD` 4eeef74 (400 `application/json`, no log)
     and when the cause check is removed (the malformed-body cases answer 503)". Add a fault-handling line to
     its unit acceptance criteria: a spool failure is a logged, retryable 503 with nothing stored; a malformed
     body stays 400. Version-history line.
   - **TS-011** (approved 1.6 → 1.7, same approval handling): TC-011.7 lists the two step-2 tests and
     "upload refusals with a problem+json 503 carry the server's detail". Version-history line.
   - **SOUP-002** FastAPI (approved 1.2 → 1.3, same approval handling): relied-on behaviour — an exception
     other than `HTTPException` raised while reading a form body is re-raised as
     `starlette.exceptions.HTTPException(400)` `from` that exception (`fastapi/routing.py:420-465`); MedHub's
     upload route class maps an `OSError` cause to a 503 problem (TASK-232, TC-007.17). Change-log line.
   - **SOUP-003** Starlette (approved 1.3 → 1.4, same approval handling): relied-on behaviour — an `OSError`
     raised while spooling a file part propagates out of `Request.form()` unchanged (only
     `MultiPartException` is mapped to 400). Change-log line.
   - **arc42** (Document Writer role): `docs/design/05-building-blocks.md` (`U-ATT-Upload` line: spool
     failure → logged 503), `docs/design/08-cross-cutting-concepts.md` §8.6 ("Error contract added by
     CR-007"), `docs/design/12-interfaces.md` (new "API contract changes of CR-007" row: upload, new response
     503 `upload-storage-unavailable`, `Retry-After: 30`, additive, documented in the OpenAPI `responses`).
   - Do **not** edit RISK-007, PRB-092, `infra/DEPLOY.md` or section 11: TASK-231 round 2 owns them and
     records this task's control (CR-007 Plan). Commit only this task's files (`git add` by path): the working
     tree also holds TASK-231's uncommitted edits.

## Verification

- `cd backend && uv run pytest tests/api/test_attachments_router.py tests/attachments tests/core/test_attachment_body_limit.py tests/api/test_error_handlers.py tests/api/test_error_logging.py tests/api/test_openapi_contract.py -q`;
  then the whole backend suite, `uv run ruff check .`, `uv run black --check .` (CI runs Black).
- `cd frontend && npm run test -- --run`, `npm run lint`, `npm run typecheck`; on Node 20 or later
  (local default is 18; CI uses 24).
- `git diff --exit-code backend/openapi/openapi.json frontend/src/api/generated/openapi.ts` after step 5 run
  twice shows no further change; the only contract difference against `HEAD` is the upload operation's 503.
- Mutation checks, recorded in the Implementation record: (a) remove the `isinstance(..., OSError)` check →
  the malformed-body cases fail; (b) remove `route_class` → the 503 and log tests fail; (c) catch
  `fastapi.HTTPException` instead of Starlette's → the 503 test fails.
- `traceability-check` on TASK-232, TS-007, TS-011, SOUP-002, SOUP-003, CR-007: 0 errors.

## Acceptance criteria

- [x] A spool failure during the upload parse answers 503 `application/problem+json`
  `upload-storage-unavailable` with `Retry-After: 30`, stores nothing, and writes one `ERROR` log record with
  the route template and errno and without the raw path or file name (SR-013 AC 1, SR-043; TC-007.17).
- [x] A malformed multipart body still answers 400 as before, and an `OSError` raised after the parse still
  answers the 500 problem (TC-007.17).
- [x] The upload form shows the 503 problem's detail (SR-027 AC 3; TC-011.7); the OpenAPI change is the
  documented 503 only, regenerated in both generated files.

## Definition of Done

- [x] Tests written first and seen failing on `HEAD` (the 503 and log tests); all suites, lint, Black and
  typecheck green; mutation checks recorded
- [x] TS-007, TS-011, SOUP-002, SOUP-003 and arc42 05, 08, 12 updated; `traceability-check` 0 errors
- [x] `graphify update .` run after the code change

## Implementation record

Software Developer role, 2026-11-16, against `HEAD` 4eeef74. Nothing committed.

**Changes.** `backend/app/api/errors.py` (`UploadStorageUnavailableProblem`, 503, `Retry-After: 30`);
`backend/app/api/routers/attachments.py` (`_SpoolFailureRoute`, set as the router's `route_class`; 503 in
the upload `responses`); `backend/tests/api/test_attachments_router.py` (`TestUploadScratchSpaceFailure`, 5
test items); `frontend/src/api/client.test.ts` (503 row of the `uploadAttachment` problem+json table);
`frontend/src/core/clinical/AttachmentUpload.test.tsx` (503 test); regenerated
`backend/openapi/openapi.json` (+10 lines) and `frontend/src/api/generated/openapi.ts` (+9 lines), the
upload operation's 503 only; records TS-007 1.13, TS-011 1.7, SOUP-002 1.3, SOUP-003 1.4 (all `in_review`,
approval record removed); arc42 05, 08, 12.

**Test first.** Before the production change the 503 and the log tests failed (400, no record); the
malformed-body (2) and the 500 tests passed on `HEAD`. The frontend tests pass on `HEAD` (no code change).

**Acceptance criteria.** AC 1: the 503 test and the log test (one `ERROR` record, `ENOSPC`, route
template, `exc_info` an `OSError`, no entry id, no file name). AC 2: the malformed-body tests (8 KB part
header, no boundary) answer 400 `application/json` with no router `ERROR` record; an `OSError` from
`store` answers the 500 `internal-error`. AC 3: the two frontend tests; the OpenAPI diff is the 503 only.

**Mutation checks** (each reverted afterwards). (a) the `isinstance(err, OSError)` check replaced by
`err is None`: the 8 KB-header 400 case fails (it has a `MultipartParseError` cause; the no-boundary case
has no cause and is not distinguishing). (b) `route_class` removed: the 503 test and the log test fail.
(c) `fastapi.HTTPException` caught instead of Starlette's: the 503 test and the log test fail.

**Verification.** Black, `ruff check` clean; backend suite 1466 passed, 10 skipped, 0 failed, 282 errors (every error is a test that needs a Docker
daemon through testcontainers, not running on this machine; the named verification set: 144 passed, 8 such errors); frontend
(Node 20.19.0) `npm test -- --run` 416 passed, `typecheck` and `lint` clean; `generate:types` leaves no
diff on a second run. `ruff format --check` lists four test files this task does not touch (pre-existing;
CI runs Black, which passes). `graphify update .` run.

## Version history

- 1.0 (2026-11-16) — Created at the CR-007 1.2 Plan stage (Software Architect role) from D-7 ("Add a code fix in CR-007"), after TASK-231 QA R1-1. `draft`.
- 1.1 (2026-11-16) — Implemented (Software Developer role); implementation record added. `in_review`.
- 1.1 (2026-11-16) — QA review round 1: APPROVED, `in_review` to `approved`; acceptance criteria and Definition of Done ticked. TS-007 1.13 and TS-011 1.7 `approved`; SOUP-002 1.3 and SOUP-003 1.4 stay `in_review` for the human.

## QA review round 1 (qa-engineer, 2026-11-16) — APPROVED

0 CRITICAL, 0 HIGH, 0 MEDIUM, 2 LOW (not blocking).

- **LOW-1** — `backend/app/api/routers/attachments.py:50` (`exc.status_code != 400`): no test
  distinguishes this check (mutant "drop the status check" passes all five tests). FastAPI only raises the
  body-parse `HTTPException` as 400, so it is defensive and practically equivalent today. Fix, the next
  time the file changes: add a case in `TestUploadScratchSpaceFailure` where the handler raises a
  non-400 Starlette `HTTPException` chained `from` an `OSError` and assert it is not mapped to 503.
- **LOW-2** — `backend/tests/api/test_attachments_router.py` (`test_spool_failure_is_logged_at_error_without_the_path_or_file_name`):
  the no-entry-id / no-file-name assertions check `record.getMessage()` only, not the formatted traceback
  (`exc_info`). QA probe (below) shows the formatted JSON record, traceback included, carries neither,
  so this is a test-strength gap, not a defect. Fix, next time: also assert on
  `logging.Formatter().formatException(record.exc_info)`.
- Observation (not a finding): with a real `OSError` raised when the temporary file is created, the
  traceback names the server's temporary directory and the random `tmpXXXX` name. That is not the request
  path, a file name or form data (SR-043 AC 4, section 8.14), and it helps the operator locate the full
  directory.
- Mutation (a) gap reported by the developer: confirmed and sufficient. The `err is None` mutant is
  killed by the 8 KB part-header case (cause `MultipartParseError`); the no-boundary case has no cause and
  only kills the "no cause check at all" mutant. Together they cover both mutants.

Verification (working tree; Docker was first not running, then started): `uv run ruff check .` clean,
`uv run black --check .` 290 unchanged; named set (`test_attachments_router.py`, `tests/attachments`,
`test_attachment_body_limit.py`, `test_error_handlers.py`, `test_error_logging.py`,
`test_openapi_contract.py`) 144 passed, 8 errors (testcontainers, no Docker); whole backend suite 1466
passed, 10 skipped, 0 failed, 282 errors (testcontainers; same count as the developer; CI runs them). Re-run once
Docker was started (Docker 24.0.5): whole backend suite 1748 passed, 10 skipped, 0 failed, 0 errors
(the 282 testcontainers tests now pass).
OpenAPI re-exported and `npm run generate:types` re-run: both generated files byte-identical (`cmp`),
`types.ts` unchanged; the contract diff against `HEAD` is the upload's 503 only. Frontend on Node 20.19.0:
41 files, 416 tests passed; `typecheck` and `lint` exit 0. Mutants (scratch copy of `backend/`,
restored and `cmp`-identical to the tree): no cause check → both malformed cases fail; `err is None` →
8 KB case fails; no `route_class` → 503 and log tests fail; `fastapi.HTTPException` → 503 and log tests
fail; `logger.warning` → log test fails; raw `request.url.path` logged → log test fails; no `exc_info` →
log test fails; re-raise the 400 → 503 test fails; drop `status_code != 400` → survives (LOW-1). Real-error
probe (no monkeypatch of `rollover`: `tempfile.tempdir` set to a missing directory, the project's
`configure_logging` JSON formatter, file name `jane.doe@example.com-scan.dcm`, a form field
`PATIENT-SECRET`): 503 `application/problem+json` `upload-storage-unavailable`, `Retry-After: 30`,
`store` not called; one ERROR record "Upload body could not be spooled for POST
/clinical-entries/{entry_id}/attachments: ENOENT (No such file or directory)" with the traceback; neither
the entry id, the file name nor the form field appears in any application log line. Starlette 1.3.1
`formparsers.py:291-294` closes the spooled files on `OSError` as well, so nothing is left open.
Records: TS-007 (approved 1.12 at `HEAD`), TS-011 (approved 1.6), SOUP-002 and SOUP-003 (approved with
approval fields at `HEAD`) were each bumped, set `in_review`, approval fields removed where present, and
given a history line (CR-007 "Never" rule met). The diff touches exactly the developer's file list for
this task; 05, 08 and 12 hold only TASK-232 lines. `traceability-check` on TASK-232, TS-007, TS-011,
SOUP-002, SOUP-003, CR-007, SR-013, SR-027, RISK-007: 0 errors. Warnings, all W5 (approved record
linking a non-approved one), expected: SR-013 and TASK-232 → RISK-007 `in_review` (TASK-231's uncommitted
RISK-007 edit), TASK-232 → TASK-231 `draft`, TASK-232 → SOUP-002 and SOUP-003 `in_review` (human approval).
