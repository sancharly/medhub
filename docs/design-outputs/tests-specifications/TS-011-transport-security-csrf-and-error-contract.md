---
id: TS-011
type: test-specification
title: Transport security, CSRF and error contract verification
status: approved
version: "1.6"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-14"
links:
  - target: SR-001
    relation: verifies
  - target: SR-031
    relation: verifies
  - target: SR-030
    relation: verifies
  - target: SR-027
    relation: verifies
tags:
  - level:unit
  - class:B
---

# TS-011 — Transport security, CSRF and error contract verification

## Scope

Software requirements covered: SR-001, SR-031; SR-030 (AC 8, upload 401) and SR-027 (AC 3, upload failure detail) through TC-011.7.
Software items under test: SI-API, SI-FE-APICLIENT.
Levels: unit, integration.

## Preconditions and environment

Build: branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 24 LTS (build stage node:24.22.2-trixie-slim; CI node-version 24) with `frontend/package-lock.json`.
Unit and service tests run with no external services (TestClient; no real proxy). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-011.1 | SR-031 | `backend/tests/api/test_security_headers.py` | Security headers are present on every response | Each header asserted by name |
| TC-011.2 | SR-031 | `backend/tests/api/test_csrf_enforcement.py` | Every mutating route requires a valid CSRF token | A missing or wrong token is refused on each router |
| TC-011.3 | SR-031 | `backend/tests/api/test_error_handlers.py`, `frontend/src/core/error/problemToMessage.test.ts` | Errors are RFC 7807 problem+json and are rendered as actionable messages | Status-to-type mapping asserted |
| TC-011.4 | SR-031 | `backend/tests/api/test_openapi_contract.py`, `frontend/src/api/client.test.ts` | The generated contract matches the implementation and the typed client uses it | Contract diff empty |
| TC-011.5 | SR-001 | `backend/tests/test_health.py`, `backend/tests/test_env_example.py` | The application serves over the documented entrypoint and requires the documented configuration | Startup asserted |
| TC-011.6 | SR-031 (AC 3) | `backend/tests/api/test_csrf_enforcement.py` (`TestCsrfExemptionIsExact`, `TestCsrfRouteInventory`; `test_is_csrf_exempt_table` includes `/api/v1/modules/x/y` as enforced; login-CSRF defence: `test_login_refuses_a_non_json_post_without_calling_the_service` for form, text/plain and multipart bodies, and `test_login_has_no_cors_so_a_cross_origin_json_post_cannot_pass_a_preflight`) | CSRF exemptions match one exact path (or one whole-path pattern); sibling and child paths are enforced; the exempt routes work without a session or token; the exempt route set equals a reviewed list | Siblings return 403 problem+json; the three exempt routes are not CSRF-blocked; a new exempt entry or route fails the inventory; login is exempt from the token, so the defence against a cross-site login is that a non-JSON body is refused with 400 before `LoginService.login` runs, and a cross-origin JSON post needs a preflight that the application, with no CORS, answers 405 |
| TC-011.7 | SR-030 (AC 8), SR-031 (AC 3), SR-027 (AC 3) | `frontend/src/api/client.test.ts` (`ApiClient uploadAttachment`: `sends FormData through request with the CSRF header`, `raises AuthError on a 401 unauthenticated problem`, `surfaces the server detail of a problem+json 413` / `400`, `raises a generic ApiError for a non-problem 500`); `frontend/src/core/clinical/AttachmentUpload.test.tsx` (`shows the server's detail when the session has ended (401)`); `frontend/src/api/problem.test-d.ts` (checked by `npm run typecheck`) | The attachment upload goes through the shared request helper: multipart body without a hand-set content type, CSRF header kept, a 401 raises `AuthError` like any other request (the redirect on a mutation's `AuthError` is verified by TASK-144), upload refusals carry the server's problem `detail`, a non-problem 500 gives the generic `ApiError`; `ProblemError` is derived from the generated `ProblemDetail` schema | All upload tests pass, and the upload form shows the server's detail for a 401; `npm run typecheck` fails if `ProblemDetail` loses `type`, `title`, `status`, `instance`, `detail` or `errors`; `npm run generate:types` leaves no diff |
| TC-011.8 | SR-031 (AC 3) | `frontend/src/api/csrf.test.ts`: `copies the medhub_csrf cookie into X-CSRF-Token, whatever else the cookie jar holds`, `keeps the whole token when it contains an equals sign`, `does not take a cookie whose name only starts or ends like the CSRF cookie`, `tolerates an absent cookie: no header and no throw`, `keeps the headers it was given and does not change the object passed in`, `sends no X-CSRF-Token on GET even when the cookie is present`, `sends X-CSRF-Token on POST` / `PUT` / `DELETE`, `sends X-CSRF-Token on PATCH (no public method uses PATCH, so the private helper is called)`, `sends a mutating request without the header, and without error, when the cookie is absent` (TASK-146, PRB-017, RISK-005) | `withCsrf` puts the `medhub_csrf` cookie value, whole, in `X-CSRF-Token`; a missing cookie gives no header and no error; the client adds the header on POST, PUT, PATCH and DELETE and never on GET, also when the cookie is present | All listed tests pass; each fails when its mechanism is changed by hand (header added without a cookie: 3 fail; cookie name matched without `=` or by `includes`: 1 each; value cut at the first `=`: 1; header renamed: 7; given headers dropped: 1; header on every method: 1 (GET); POST, PUT, PATCH or DELETE dropped from the mutating set: 1 each) |
| TC-011.9 | SR-031 (AC 3, contract) | `frontend/src/api/generated/openapiDrift.test.ts`: `openapi.ts equals the output of the generator for backend/openapi/openapi.json`, `the check notices a schema change that was not regenerated` (TASK-146, PRB-017, RISK-005) | The committed `frontend/src/api/generated/openapi.ts` is byte-identical to what `openapi-typescript` generates from the committed `backend/openapi/openapi.json`, so a hand edit of the generated file or a schema change without `npm run generate:types` fails the unit tests (CI `openapi-lint` repeats the comparison from a fresh backend export) | Both tests pass; a one-token hand edit of `openapi.ts` fails the first, a renamed schema in `openapi.json` fails the first |

## Acceptance criteria (class B unit level, §5.5.3)

- Client CSRF unit (`api/csrf.ts`, §5.5.3): boundary, only the cookie named exactly `medhub_csrf` is read and a value containing `=` is kept whole; fault handling, an absent cookie neither throws nor sets a header (TC-011.8). Coverage in the TASK-146 run: 100 % statements, branches and lines.
- Boundary: CSRF exemption list matches exactly, not by prefix (PRB-003; TC-011.6).
- Fault handling: a malformed request produces a problem document, never a stack trace.

## Notes

TLS and HSTS terminate at the reverse proxy and are verified at system level in TR-001's environment section, not by a unit test.

## Version history

- 1.2 (2026-11-02) — Status `in_review`: TC-011.6 added (TASK-139, PRB-003): exact CSRF exemptions, siblings enforced, route inventory. Boundary criterion updated. Approval record cleared; QA/human re-approve.
- 1.2 (2026-11-02) — QA review (TASK-139): approved (`in_review → approved`).
- 1.3 (2026-11-08) — TASK-202: TC-011.6 names the login-CSRF defence tests and the module-router assertion (TASK-139 QA findings 1 and 2). Content change, `in_review`.
- 1.3 (2026-11-08) — QA review of TASK-202 (round 2): `approved` (status only; content unchanged).
- 1.4 (2026-11-14) — TASK-143 (CR-006, PRB-019): TC-011.7 added (upload through `request()`, 401 raises `AuthError`, problem detail on upload failure, `ProblemError` derived from the schema); `verifies` SR-030 and SR-027 added. Content change, `in_review`; QA/human re-approve.
- 1.4 (2026-11-14) — TASK-143 QA round 1 (R1-1, R1-2, R1-3): TC-011.7 adds the `AttachmentUpload` 401 message test, says the 401 raises `AuthError` (redirect: TASK-144) and names the six schema fields the type test covers. Still `in_review`.
- 1.4 (2026-11-14) — QA review of TASK-143 (round 2): `approved` (status only; content unchanged).
- 1.5 (2026-11-14) — TASK-146 (CR-006 D-9; PRB-017): added TC-011.8 (`api/csrf.ts` unit tests and the method gate of the client) and TC-011.9 (generated types do not drift from the committed schema), and a unit acceptance criterion. Content change, so the approval of 1.4 is cleared: `in_review`.
- 1.5 (2026-11-14) — QA review of TASK-146 (round 1): `approved` (status only; content unchanged).
- 1.6 (2026-11-14) — TASK-225 (QA of TASK-146): TC-011.9 pass criteria corrected: a renamed schema in `openapi.json` fails the first test, not both. Content change on an approved record, so the 1.5 approval record is cleared: `in_review`.
- 1.6 (2026-11-15) — QA review of TASK-225 (round 2): `approved` (status only; content unchanged).
