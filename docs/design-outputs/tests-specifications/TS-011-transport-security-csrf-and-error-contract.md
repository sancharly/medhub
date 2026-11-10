---
id: TS-011
type: test-specification
title: Transport security, CSRF and error contract verification
status: approved
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-08"
links:
  - target: SR-001
    relation: verifies
  - target: SR-031
    relation: verifies
tags:
  - level:unit
  - class:B
---

# TS-011 — Transport security, CSRF and error contract verification

## Scope

Software requirements covered: SR-001, SR-031.
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

## Acceptance criteria (class B unit level, §5.5.3)

- Boundary: CSRF exemption list matches exactly, not by prefix (PRB-003; TC-011.6).
- Fault handling: a malformed request produces a problem document, never a stack trace.

## Notes

TLS and HSTS terminate at the reverse proxy and are verified at system level in TR-001's environment section, not by a unit test.

## Version history

- 1.2 (2026-11-02) — Status `in_review`: TC-011.6 added (TASK-139, PRB-003): exact CSRF exemptions, siblings enforced, route inventory. Boundary criterion updated. Approval record cleared; QA/human re-approve.
- 1.2 (2026-11-02) — QA review (TASK-139): approved (`in_review → approved`).
- 1.3 (2026-11-08) — TASK-202: TC-011.6 names the login-CSRF defence tests and the module-router assertion (TASK-139 QA findings 1 and 2). Content change, `in_review`.
- 1.3 (2026-11-08) — QA review of TASK-202 (round 2): `approved` (status only; content unchanged).
