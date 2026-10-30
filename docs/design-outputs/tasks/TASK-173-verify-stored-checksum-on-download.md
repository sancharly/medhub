---
id: "TASK-173"
type: task
title: "Verify the stored checksum on every attachment download"
status: draft
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

- [ ] CR-002 **AC-5** / SR-013 AC 5: substituted object refused with an error and an audit
      FAILURE event; unmodified object downloads with the same bytes; DICOM covered; the tests
      fail without the check.
- [ ] CR-002 **AC-15** (SR-013 part): TS-007 `verifies` SR-013 and lists TC-007.6..8.

## Verification

```sh
cd backend && uv run pytest tests/attachments modules/dicom_viewer/tests -v
cd backend && uv run pytest --cov=app --cov-fail-under=85
cd backend && uv run ruff check . && uv run mypy app
cd frontend && npm run generate:types && npx tsc --noEmit && npm test
git diff --exit-code backend/openapi/openapi.json frontend/src/api/generated/openapi.ts  # after commit: regenerated files committed
```

## Definition of Done

- [ ] Lint, type-check and both suites pass; coverage ≥ 85 %.
- [ ] OpenAPI regenerated, and the `openapi-lint` CI job is green.
- [ ] Audit event emitted for the refusal (SR-023).
- [ ] `traceability-check` shows no error for this task and TS-007.
