---
id: "TASK-127"
type: task
title: "Surface the security model in OpenAPI (remediation)"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-031"
    relation: implements
  - target: "NFR-006"
    relation: implements
  - target: "TASK-068"
    relation: relates_to
  - target: "TASK-128"
    relation: relates_to
tags: ["phase:4-api-layer", "remediation-of:TASK-068", "original-id:TASK-068a"]
---

- **Phase:** 4 — API layer
- **Implements / restores:** SR-031, NFR-006; remediates TASK-068
- **Depends on:** TASK-068, TASK-069a
- **Branch:** `feature/openapi-security`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-068 verdict **PARTIAL**

*Originally filed as TASK-068a.*

## Objective

The OpenAPI `cookieAuth` security scheme is **defined but never applied** to any operation (root
`security` is `[]`), and the `X-CSRF-Token` header is undocumented — so the contract does not surface the
deny-by-default + CSRF model it claims. The contract tests only assert the scheme exists.

## Implementation detail

- In `app/api/openapi.py`, apply the `cookieAuth` requirement to all protected operations (exempt the
  public ones), and document the `X-CSRF-Token` header on state-changing operations.
- Strengthen the contract test to assert protected ops reference the scheme and that state-changing ops
  document the CSRF header.
- Consolidate the duplicate `app/export_openapi.py` / `scripts/export_openapi.py` to the one CLAUDE.md references.

## Acceptance criteria

- [x] Every protected operation declares the cookie security requirement; public routes do not.
- [x] State-changing operations document `X-CSRF-Token`.
- [x] Contract test fails if an operation omits the security requirement.

## Definition of Done

- [x] Lint + type-check pass
- [x] OpenAPI regenerated, redocly lint passes, parity check green
- [x] Contract tests updated and passing (3 new tests in `TestOpenAPISecurityRequirements`)
- [x] Traceability row updated (SR-031 → TASK-068a → tests)
- [x] Security review completed — public-route set (`/api/v1/auth/login`, `/api/v1/activation/{token}`, `/healthz`) confirmed correct; all other routes require `cookieAuth`; state-changing protected routes require `X-CSRF-Token` per contract.

## Implementation notes (2026-06-30)

- `backend/app/api/openapi.py`: `_PUBLIC_PATHS` frozenset defines unauthenticated routes; `customize_openapi` now iterates all paths and applies `security: [{cookieAuth: []}]` to non-public operations and `X-CSRF-Token` parameter to state-changing non-public operations.
- `backend/scripts/export_openapi.py`: consolidated to delegate to `app.export_openapi.main`; no duplicate logic.
- `backend/tests/api/test_openapi_contract.py`: `TestOpenAPISecurityRequirements` class with 3 assertions; `TestOpenAPIExport` updated to use the canonical `-m app.export_openapi` invocation.

## QA sign-off

- **Date:** 2026-06-30
- **Reviewer:** QA Engineer agent (phase-4 audit remediation)
- **Evidence:** 11 contract tests pass; `openapi.json` regenerated confirming `security: [{cookieAuth: []}]` on all protected paths and `X-CSRF-Token` on all state-changing protected paths; ruff + mypy clean; 484 total tests pass.
