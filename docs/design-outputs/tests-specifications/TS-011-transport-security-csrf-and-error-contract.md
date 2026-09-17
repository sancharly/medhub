---
id: "TS-011"
type: test-specification
title: "Transport security, CSRF and error contract verification"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links:
  - target: "SR-001"
    relation: verifies
  - target: "SR-031"
    relation: verifies
tags: ["level:unit", "class:B"]
---

# TS-011 — Transport security, CSRF and error contract verification

## Scope

Software requirements covered: SR-001, SR-031.
Software items under test: SI-API, SI-FE-APICLIENT.
Levels: unit, integration.

## Preconditions and environment

Build: branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 20 with `frontend/package-lock.json`.
Unit and service tests run with no external services (TestClient; no real proxy). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: [ADD-004](../architecture/ADD-004-soup-list.md).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-011.1 | SR-031 | `backend/tests/api/test_security_headers.py` | Security headers are present on every response | Each header asserted by name |
| TC-011.2 | SR-031 | `backend/tests/api/test_csrf_enforcement.py` | Every mutating route requires a valid CSRF token | A missing or wrong token is refused on each router |
| TC-011.3 | SR-031 | `backend/tests/api/test_error_handlers.py`, `frontend/src/core/error/problemToMessage.test.ts` | Errors are RFC 7807 problem+json and are rendered as actionable messages | Status-to-type mapping asserted |
| TC-011.4 | SR-031 | `backend/tests/api/test_openapi_contract.py`, `frontend/src/api/client.test.ts` | The generated contract matches the implementation and the typed client uses it | Contract diff empty |
| TC-011.5 | SR-001 | `backend/tests/test_health.py`, `backend/tests/test_env_example.py` | The application serves over the documented entrypoint and requires the documented configuration | Startup asserted |

## Acceptance criteria (class B unit level, §5.5.3)

- Boundary: CSRF exemption list matches exactly, not by prefix (currently PRB-003).
- Fault handling: a malformed request produces a problem document, never a stack trace.

## Notes

TLS and HSTS terminate at the reverse proxy and are verified at system level in TR-001's environment section, not by a unit test.
