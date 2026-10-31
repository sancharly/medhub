---
id: "TASK-173"
type: task
title: "Verify the stored checksum on every attachment download"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "SR-013"
    relation: implements
  - target: "RISK-012"
    relation: mitigates
  - target: "CR-002"
    relation: relates_to
  - target: "PRB-043"
    relation: relates_to
  - target: "RISK-002"
    relation: relates_to
  - target: "RISK-003"
    relation: relates_to
  - target: "RISK-007"
    relation: relates_to
  - target: "RISK-006"
    relation: relates_to
tags: ["security", "data-integrity", "cr:CR-002", "issue:sancharly/medhub#33", "control:protective"]
---

# TASK-173 — Verify the stored checksum on every attachment download

- **Software item / unit:** SI-ATTACH `U-ATT-Fetch` (ADD-012); SI-AUDIT (ADD-013) as a consumer
- **Depends on:** none. It is independent of the Q-1 answer and can start at once, in parallel
  with TASK-172 and TASK-174.
- **Branch:** `bug/minio-object-store`
- **Size:** M (service, error type, router OpenAPI, tests, TS-007, plus the generated contract
  files)
- **Needs:** no Docker, apart from the real-database tests of the full suite

## Objective

SR-013 AC 5: an attachment whose stored bytes do not match the SHA-256 recorded at upload is never
served. The client gets an error, and the audit log records a FAILURE for that attachment and
actor. This closes the path in RISK-012 where a substituted or planted object is served as the
original (PRB-043).

## Interfaces to honor

- Every read goes through `AttachmentService.open` (CR-002 A-3). Callers are
  `backend/app/api/routers/attachments.py:89` and
  `backend/modules/dicom_viewer/dicom_viewer/router.py:30`. Both are covered by changing `open`
  only. Confirm that no other read of `get_object` exists (`grep -rn get_object backend/`).
- `Attachment.checksum` is the lowercase hex SHA-256 written by `store()`. The column is
  `NOT NULL`.
- Errors are RFC 7807, raised as a `ProblemError` subclass in `backend/app/api/errors.py`. Follow
  the existing `type` URI convention in that file.
- Contract rule (`CLAUDE.md`): a new documented response means you regenerate
  `backend/openapi/openapi.json` and `frontend/src/api/generated/openapi.ts`. Never hand-edit them.

## Implementation detail

1. In `AttachmentService.open`, after `get_object`, compute `hashlib.sha256(data).hexdigest()`
   and compare it with `attachment.checksum` using `hmac.compare_digest`.
2. On a mismatch:
   - record `AuditAction.ATTACHMENT_ACCESS` with `AuditOutcome.FAILURE`, the actor and the
     attachment id;
   - raise a new `AttachmentIntegrityError` (HTTP 502, because the store returned content that
     is not what was stored). Its `detail` names the attachment id and contains no hash values or
     content.
   - Return no bytes.
   - **Check** that the FAILURE audit row is committed even though the request ends in an error.
     Follow the pattern the authorization-denied path uses. If the transaction would roll it
     back, record it the same way that path does. Do not invent a second mechanism.
3. On a match, behaviour is unchanged (SUCCESS audit, same bytes).
4. Declare the 502 response on the attachment download route and the DICOM viewer route, then
   regenerate:
   - `cd backend && uv run python -m app.export_openapi --output openapi/openapi.json`;
   - `cd frontend && npm run generate:types`;
   - fix any type errors.
5. **TS-007**: add TC-007.6 (substituted object: no content, 502 problem, audit FAILURE),
   TC-007.7 (unmodified object: identical bytes, audit SUCCESS) and TC-007.8 (a DICOM attachment
   through the viewer route is refused when substituted). Each `verifies` SR-013 AC 5.

## Tests (write first)

- Service unit tests with a fake storage that returns altered bytes, then the original bytes.
  Assert the exception, the audit record (outcome, actor, target) and that no data is returned.
- API test through `GET` on the attachment download route: status, problem `type`, and no body
  bytes from the object.
- DICOM viewer router test with a substituted DICOM object.
- **Mutation check:** remove the comparison temporarily, show that the three negative tests fail,
  restore it, and record the result in the evidence (CR-002 AC-5 "fail when the check is
  removed").

## Acceptance criteria

- [x] CR-002 **AC-5** / SR-013 AC 5: substituted object refused with an error and an audit
      FAILURE event; unmodified object downloads with the same bytes; DICOM covered; the tests
      fail without the check.
- [x] CR-002 **AC-15** (SR-013 part): TS-007 `verifies` SR-013 and lists TC-007.6..8.

## Verification

```sh
cd backend && uv run pytest tests/attachments modules/dicom_viewer/tests -v
cd backend && uv run pytest --cov=app --cov-fail-under=85
cd backend && uv run ruff check . && uv run mypy app
cd frontend && npm run generate:types && npx tsc --noEmit && npm test
git diff --exit-code backend/openapi/openapi.json frontend/src/api/generated/openapi.ts  # after commit: regenerated files committed
```

## Definition of Done

- [x] Lint, type-check and both suites pass; coverage ≥ 85 %.
- [x] OpenAPI regenerated, and the `openapi-lint` CI job is green.
- [x] Audit event emitted for the refusal (SR-023).
- [x] `traceability-check` shows no error for this task and TS-007.

## Developer handoff (draft to in_review)

- **Implementation:** `AttachmentService.open` hashes the bytes returned by `get_object` and
  compares with `hmac.compare_digest` against `Attachment.checksum`. A mismatch records
  `ATTACHMENT_ACCESS` / FAILURE (actor, attachment id) and raises
  `AttachmentIntegrityError` (502, type `attachment-integrity-failure`, detail names only the
  attachment id). Only `open` reads `get_object`; both callers (attachment route, DICOM
  `/studies/{id}` route) are covered.
- **Audit persistence:** the authorization-denied path calls `audit_svc.record` and then raises, and
  `get_db` rolls the session back on any exception, so that row is lost with the request (see
  PRB candidate below). The check therefore commits its FAILURE row immediately through
  `AuditService.record(..., durable=True)` (new, default off; `AuditRepository.commit`). It is the
  only new mechanism. `backend/tests/attachments/test_attachment_integrity_persistence.py` proves
  persistence with the real `get_db` against PostgreSQL.
- **Contract:** 502 declared on `GET /attachments/{attachment_id}` and on the DICOM route;
  `openapi.json` and `openapi.ts` regenerated (3 and 7 lines).
- **Mutation check (CR-002 AC-5):** with the comparison replaced by `if False:`, the substituted-object
  tests fail: service unit (`test_open_substituted_object_is_refused_and_audited_as_failure`), API
  (`TestFetchSubstitutedAttachment`), DICOM route (`TestSubstitutedDicomObject`) and persistence
  test (4 failed, all others in those sets pass). With `durable=False` the unit and persistence
  tests fail. Source restored afterwards.
- **TS-007 1.3** adds TC-007.6..8 (status `in_review`, approval cleared).

## QA review (2026-10-30)

**Verdict: APPROVED** (`in_review → approved`; TS-007 1.3 `in_review → approved`). QA ticked AC-5,
AC-15 (SR-013 part) and the four Definition of Done items. There is no CRITICAL or HIGH finding.
The `openapi-lint` item is ticked on its local equivalent (regeneration is byte-identical); the CI
run itself is seen at push.

**Rerun by QA** (working tree of `bug/minio-object-store` at `2e32431` plus the TASK-173 changes):

- `uv run pytest --cov=app --cov-fail-under=85` → 504 passed, total coverage 91.74 %. It includes
  `tests/attachments/test_attachment_integrity_persistence.py` (testcontainers `postgres:16`).
- `uv run pytest modules/dicom_viewer/tests` → 19 passed. It must run apart from `tests/`: running
  both in one session fails with `ImportPathMismatchError` on `tests.conftest`.
- `uv run ruff check .` → clean; `uv run mypy app` → no issues in 124 files.
- `export_openapi` and `npm run generate:types` rerun → `openapi.json` and `openapi.ts`
  byte-identical to the working tree. `npx tsc --noEmit` clean; `npx vitest run` → 155 passed.
- Mutation, on a scratch copy of `backend/` (working tree untouched): comparison replaced by
  `if False:` → 4 failed (the service unit, API, persistence and DICOM substituted-object tests),
  all other tests in those sets pass. `durable=True` → `False` → 2 failed (service unit,
  persistence).
- `traceability-check` (fallback parser) over TASK-173, TS-007, SR-013, RISK-012, RISK-003,
  CR-002, PRB-043 → 0 errors. Warnings: SR-013 → RISK-012 `in_review` (W5), and after this
  approval TASK-173 → RISK-012 `in_review` (W5). Both are expected until the human approves
  RISK-012 at TASK-181. RISK-012's W3 (no incoming `mitigates`) clears with this task.

**Review of the durable commit.** `AuditService.record(..., durable=True)` calls
`AuditRepository.commit()`, which commits the whole request session, not only the audit row. In
`open()` the only pending writes at that point are audit rows: the `AUTHZ_ALLOWED` row from
`AuthorizationService.authorize` and the FAILURE row. The route is a read, so nothing is partly
written. The refused read is the only caller. The 502 detail is
`Attachment <id> failed its integrity check and was not served.`, plus `instance` (the request
path). It carries no hash and no content, and the unit and API tests assert this.

**Findings (non-blocking)**

- **LOW: the `durable` flag commits the caller's whole unit of work.** Location:
  `backend/app/audit/service.py:61-62`, `backend/app/db/repositories/audit_repo.py:23-25`. A later
  caller on a write path would commit half-done business writes with its audit row. → Fix: state in
  the docstring that `durable=True` commits every pending change in the session and is only for
  read paths. The app-wide fix (the PRB below) should replace the flag with an audit write on its
  own session.
- **LOW: the 502 is declared without its problem body.** Location:
  `backend/app/api/routers/attachments.py:85`, `backend/modules/dicom_viewer/dicom_viewer/router.py:24`.
  The generated `openapi.ts` types the body as `content?: never`, but the server sends
  `application/problem+json`. → Fix: add `"content": {"application/problem+json": {"schema":
  {"$ref": "#/components/schemas/ProblemDetail"}}}`, as `backend/app/api/openapi.py:115-118` does,
  then regenerate both files.
- **LOW: an extra reload after the commit.** Location: `backend/app/attachments/service.py:153`.
  The session factory keeps `expire_on_commit=True`, so `attachment.id` in the message reloads the
  row after the commit. → Fix: use the `attachment_id` parameter.

**Pre-existing (not blocking)**

- `get_db` rolls back every audit row written before a `ProblemError`, app-wide. QA reproduced this
  with a throwaway test (real `get_db`, PostgreSQL): a PATIENT reading another patient's attachment
  gets 403 and the `AUTHZ_DENIED` row is not in the database. A PRB is recommended (see the QA
  report to the orchestrator).
- `ruff format --check` would reformat `tests/api/test_openapi_contract.py` and
  `tests/test_env_example.py`. Neither file is in this diff, and CI does not run the format check.
- The new persistence test uses floating `postgres:16`, the same as `tests/db/conftest.py:14` and
  `tests/db/test_migration.py:26`. This is the existing testcontainers pin gap.
