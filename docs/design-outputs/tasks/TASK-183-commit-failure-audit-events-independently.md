---
id: "TASK-183"
type: task
title: "Commit failure audit events independently of the request transaction"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "SR-023"
    relation: implements
  - target: "RISK-006"
    relation: mitigates
  - target: "CR-002"
    relation: relates_to
  - target: "PRB-052"
    relation: relates_to
  - target: "TASK-173"
    relation: relates_to
  - target: "SR-013"
    relation: relates_to
  - target: "ADD-013"
    relation: relates_to
tags: ["security", "audit", "cr:CR-002", "control:design"]
---

# TASK-183 — Commit failure audit events independently of the request transaction

- **Software item / unit:** SI-AUDIT `U-AUD-Writer` (ADD-013). Consumers touched: SI-ATTACH
  `U-ATT-Fetch` (ADD-012) and the DICOM viewer study route.
- **Depends on:** TASK-173 (approved and committed: it introduced the `durable` flag this task
  removes). It is independent of the object-store tasks (TASK-174..179) and of the Q-1 answer.
  It shares no source file with TASK-174..179. To keep one commit per task in the shared working
  tree, start it after TASK-174 is committed. It must be committed before Checkpoint A.
- **Branch:** `bug/minio-object-store`
- **Size:** M (5 source files: audit service, audit repository, attachment service, two route
  declarations; new real-database tests; the generated contract files; TS-009, ADD-013, arc42 §8.4)
- **Needs:** a Docker daemon for the testcontainers PostgreSQL tests
- **Design:** [ADR-0016](../../design/adr/0016-failure-audit-events-on-own-transaction.md) (Proposed)

## Objective

SR-023 AC 1 and AC 2 for failures, which PRB-052 found unmet: every audit event that records a
failure or a refusal stays in `audit_log` after the request ends in an error response. One
mechanism, inside `AuditService`, replaces TASK-173's `durable=True`, which commits the caller's
whole unit of work. This is a design control of RISK-006 (new cause: audit rows rolled back with
the failed request).

It also closes the other two LOW QA findings of TASK-173, which touch the same lines.

## Interfaces to honor

- `AuditService.record(actor, action, target_type, target_id, outcome, ip)` keeps its signature,
  minus `durable`. No caller changes apart from removing `durable=True` at
  `backend/app/attachments/service.py:150`.
- `AuditRepository` stays append-only: no get, list, update or delete (SR-023 AC 5).
- `get_db` (`backend/app/db/repositories/session.py`) is **not** changed.
- Contract rule (`CLAUDE.md`): a changed response declaration means you regenerate
  `backend/openapi/openapi.json` and `frontend/src/api/generated/openapi.ts`. Never hand-edit them.

## Implementation detail

1. **`AuditRepository.add_independent(log)`**: opens `Session(bind=self._session.get_bind())`,
   adds the row, commits, and closes the session in `finally`. A failure raises. Remove
   `AuditRepository.commit()`.
2. **`AuditService.record`**: an event is *independent* when `outcome is AuditOutcome.FAILURE` or
   `action` is in a module-level frozenset `_INDEPENDENT_ACTIONS = {AuditAction.ACCOUNT_LOCKOUT}`.
   An independent event goes through `add_independent`, and any other event through `add` (as
   now). Remove the `durable` parameter. In the docstring, state the rule and that an independent
   row is not atomic with the request (ADR-0016).
3. **Affected paths.** No code change at the call sites, but each one gets a test (below):
   - `AUTHZ_DENIED`: `backend/app/authz/service.py:74-82`, then 403;
   - `LOGIN_FAILURE`: `backend/app/auth/login.py:80-115` (unknown email, locked account, wrong
     password or inactive account), then 401 at `backend/app/api/routers/auth.py:63-64`;
   - `ACCOUNT_LOCKOUT`: `backend/app/auth/lockout.py:80-88`, recorded inside the failing login
     (outcome SUCCESS, so the outcome rule alone misses it). **Not listed in PRB-052.** Add it to
     PRB-052's Investigation when it is resolved;
   - `ACTIVATION_FAILED`: `backend/app/identity/activation.py:69-77`, then 401;
   - `DICOM_STUDY_READ` FAILURE: `backend/modules/dicom_viewer/dicom_viewer/router.py:34-43`,
     then 403;
   - `ATTACHMENT_ACCESS` FAILURE: `backend/app/attachments/service.py:143-154`, then 502 (TASK-173).
     Remove `durable=True`.
4. **TASK-173 LOW 3 (reload):** build the `AttachmentIntegrityError` message from the
   `attachment_id` parameter, not `attachment.id` (`backend/app/attachments/service.py:153`).
   With no commit on the request session, the reload goes away anyway. The parameter makes this
   explicit.
5. **TASK-173 LOW 2 (502 body):** on `GET /attachments/{attachment_id}`
   (`backend/app/api/routers/attachments.py:85`) and the DICOM `/studies/{attachment_id}` route
   (`backend/modules/dicom_viewer/dicom_viewer/router.py:24`), declare the 502 with
   `"content": {"application/problem+json": {"schema": {"$ref": "#/components/schemas/ProblemDetail"}}}`,
   as `backend/app/api/openapi.py:115-118` does. Then regenerate:
   - `cd backend && uv run python -m app.export_openapi --output openapi/openapi.json`;
   - `cd frontend && npm run generate:types`;
   - fix any type errors (none expected; the frontend does not consume the 502 body today).
6. **Records:**
   - **TS-009** to 1.2 (approval record cleared, `in_review`). Update the build line in
     "Preconditions" and add:
     - TC-009.4 (`AUTHZ_DENIED` persists after 403);
     - TC-009.5 (`LOGIN_FAILURE` for each of the three branches, and `ACCOUNT_LOCKOUT` on the
       threshold failure, persist after 401);
     - TC-009.6 (`ACTIVATION_FAILED` persists after 401);
     - TC-009.7 (`DICOM_STUDY_READ` FAILURE persists after 403);
     - TC-009.8 (a pending business row in the same request is rolled back while the FAILURE row
       persists; a SUCCESS event of a failed request is rolled back).

     All of them are *real DB* and `verifies` SR-023. Note that TC-007.6's persistence test now
     runs without `durable`.
   - **ADD-013** to 1.1 (approval record cleared, `in_review`): `U-AUD-Writer` writes failure and
     refusal events on an independent transaction (ADR-0016). Add ADR-0016 to the governing
     decisions.
   - **arc42** `docs/design/08-cross-cutting-concepts.md` §8.4: one sentence on the rule and a link
     to ADR-0016. Narrative only. The Document Writer may take it.
   - **PRB-052**: `## Resolution` (fix, commit, tests, mutation result), Investigation amended
     with `ACCOUNT_LOCKOUT` and with "no released version exists" (see the human's answer to the
     notification question in CR-002), and status `resolved`. Not `closed`.

## Tests (write first)

Each test sends the request through `create_app()` with the real `get_db` against a PostgreSQL
testcontainer (pattern: `backend/tests/attachments/test_attachment_integrity_persistence.py`).
It receives the error status and then queries `audit_log` on a **separate** session for the
row (action, outcome, actor or target). Redis is `fakeredis` (already a dev dependency). Each
test deletes its `audit_log` rows, because independent rows commit outside any test transaction.

- `backend/tests/audit/test_failure_audit_persistence.py`:
  - `AUTHZ_DENIED`: a PATIENT reads another patient's attachment → 403 → row present (PRB-052
    reproduction);
  - `LOGIN_FAILURE` × 3 branches → 401 → row present; the 5th wrong password → `ACCOUNT_LOCKOUT`
    row present as well;
  - `ACTIVATION_FAILED` with a wrong token → 401 → row present;
  - atomicity: a test-only route adds a business row (for example a `Group`) and records an
    `AUTHZ_DENIED`, then raises. After the response the business row is **absent** and the audit
    row is **present**. A SUCCESS event recorded before the raise is absent.
- `backend/modules/dicom_viewer/tests/test_failure_audit_persistence.py`: `DICOM_STUDY_READ`
  FAILURE on a denied study → 403 → row present. (It runs apart from `tests/`; see TASK-173 QA.)
- Unit (`backend/tests/audit/test_audit_writer.py`): FAILURE → `add_independent`; SUCCESS → `add`;
  `ACCOUNT_LOCKOUT` → `add_independent`; `record` has no `durable` parameter.
- Update `backend/tests/attachments/test_attachment_fetch.py:133` (asserts `durable`) to assert
  `add_independent` instead.
- Contract: `backend/tests/api/test_openapi_contract.py` (or a new case) asserts the 502 of both
  routes references `ProblemDetail` under `application/problem+json`.
- **Mutation check:** route every event through `add` (the old behaviour). Show that every
  persistence test above, and TC-007.6's persistence test, fails. Restore, and record the counts
  in the handoff (CR-002 AC-21).

## Acceptance criteria

- [ ] CR-002 **AC-21** / SR-023 AC 1, AC 2: each affected FAILURE or refusal event persists after
      the error response, tested against a real database per path; the tests fail with the old
      behaviour.
- [ ] CR-002 **AC-22**: no `durable` flag and no session-wide commit in the audit path; a pending
      business write is not committed by an audit event.
- [ ] CR-002 **AC-23**: both 502 responses declare the `ProblemDetail` problem body in the
      regenerated contract.

## Verification

```sh
cd backend && uv run pytest tests/audit tests/attachments tests/auth tests/identity -v
cd backend && uv run pytest modules/dicom_viewer/tests -v      # separate session
cd backend && uv run pytest --cov=app --cov-fail-under=85
cd backend && uv run ruff check . && uv run mypy app
grep -rn "durable" backend/app backend/modules                 # expect no match
cd frontend && npm run generate:types && npx tsc --noEmit && npm test
git diff --exit-code backend/openapi/openapi.json frontend/src/api/generated/openapi.ts  # after commit
```

## Definition of Done

- [ ] Lint, type-check and both suites pass; coverage ≥ 85 %.
- [ ] OpenAPI regenerated; the `openapi-lint` CI job is green.
- [ ] Mutation result recorded below.
- [ ] TS-009 1.2, ADD-013 1.1 `in_review`; PRB-052 `resolved` with `## Resolution`.
- [ ] `traceability-check` shows no error for TASK-183, TS-009, ADD-013, SR-023, RISK-006,
      PRB-052 and CR-002.
