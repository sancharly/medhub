---
id: ADD-005
type: architecture-doc
title: API Layer / Routers (SI-API)
status: approved
version: "1.5"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-16"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-16"
approved_digest: 850ff90d111086f5ef1025df11c9cc0ff486aa3c86d482fa6f519c586c1a3269
approval_note: self-approved
links:
  - target: SR-001
    relation: implements
  - target: SR-008
    relation: implements
  - target: SR-026
    relation: implements
  - target: SR-031
    relation: implements
  - target: RISK-001
    relation: relates_to
  - target: RISK-005
    relation: relates_to
  - target: RISK-007
    relation: relates_to
  - target: SOUP-001
    relation: relates_to
  - target: SOUP-002
    relation: relates_to
  - target: SOUP-003
    relation: relates_to
  - target: SOUP-004
    relation: relates_to
  - target: SOUP-005
    relation: relates_to
  - target: SOUP-006
    relation: relates_to
  - target: SOUP-007
    relation: relates_to
  - target: SOUP-017
    relation: relates_to
  - target: SOUP-024
    relation: relates_to
  - target: SR-042
    relation: implements
  - target: SR-043
    relation: implements
  - target: SR-023
    relation: implements
  - target: RISK-006
    relation: relates_to
tags:
  - software-item:SI-API
  - class:B
  - layer:backend
---

# ADD-005 — API Layer / Routers (SI-API)

## Responsibility

HTTP endpoints, request/response DTOs, validation, error formatting, AuthZ dependency wiring

## Software units (IEC 62304 §5.4.1)

- `U-API-Routers` — endpoint definitions per resource (auth, accounts, groups, appointments, clinical, attachments, consents, modules).
- `U-API-DTO` — Pydantic request/response schemas (camelCase, FHIR-traceable).
- `U-API-ErrorHandler` — RFC 7807 problem+json mapping (SR-027.3, api-design.md).
- `U-API-Deps` — DI providers: current session, current user, `authorize(...)` guard.
- `U-API-ClientAddress` — pure ASGI middleware, mounted first: applies the trusted-proxy rule of
  SR-042 AC 1 to AC 3 with the `TRUSTED_PROXIES` setting and publishes the originating client
  address in `request.state` and a `ContextVar` for the audit writer and the rate limit. Gunicorn's
  own forwarded-header handling is off ([ADR-0019](../../design/adr/0019-originating-client-address-trusted-proxy-rule.md)).
- `U-API-RateLimit` — anonymized-data retrieval limit keyed on the originating client address,
  atomic increment (`INCR` and `EXPIRE NX` in one `MULTI`/`EXEC`), fixed 3600 s window from the
  first counted attempt, 5 attempts, refused before the code is evaluated; a request with no peer
  address is refused (SR-042 AC 4, AC 5; ADR-0013 values).
- `U-API-Security` — CSRF exemptions are an exact set of paths, the activation route matched as
  one path segment; a route-inventory test keeps the set reviewed (SR-031 AC 3).
- `U-API-Routers` — the routers ask `AuthorizationService` for every access decision and compare
  no role themselves: `account:unlock`, `module:list`, `consent:grant`/`revoke`/`list` and
  `patient_roster:list` are decided in `U-AUTHZ-Policy` (ADD-007), and the account routers apply
  the non-clinical projection when `requires_admin_projection(actor)` says so (SR-005, SR-009,
  SR-023 AC 7).
- `U-API-ErrorHandler` — also answers `503` (`session-cap-contention`, `Retry-After: 1`) and `400`
  (`validation-error`, rule `filename_max_bytes`); the 500 handler logs the matched route
  template, never the raw path (section 12; SR-043 AC 4).
- The API process installs the shared log redaction filter (SR-043 AC 2) and binds the configured
  Celery app as the process default in its lifespan (`_bind_celery_app()`, see ADD-017).
- **CR-006 (ADR-0022; TASK-136, implemented):** `U-API-Deps` and every router that makes a blocking call
  are plain `def`, so FastAPI runs them in the worker-thread pool; a handler that must stay `async`
  (the attachment upload) calls its service through `run_in_threadpool`. A static test keeps any
  `async def` in `app/api` from calling a blocking client. The lifespan applies
  `API_THREADPOOL_SIZE` to AnyIO's default limiter and refuses to start when it exceeds
  `DB_POOL_SIZE + DB_MAX_OVERFLOW` (ADD-016) (SR-026 AC 5).
- **CR-006 (ADR-0021; TASK-135, implemented):** the attachment upload route has a byte-counting body
  guard (`AttachmentBodyLimitMiddleware`) that refuses an over-limit body after the maximum plus one chunk (SR-013 AC 6), with the
  existing problem type, so the OpenAPI document is unchanged.
- **CR-006 (TASK-227, ADR-0023):** every router and `U-API-Deps` provider gets its database session
  through the one alias `DbSession` (`Depends(get_db, scope="function")`, ADD-016). The commit or
  rollback of the request therefore runs before the response is sent, and a failed commit is a 5xx
  problem response (SR-012 AC 5, SR-023 AC 10). A route that declared plain `Depends(get_db)` would get
  a second session in the same request; a route-walking test refuses that. No path, status code or
  schema changes: the OpenAPI document is unchanged.
- **CR-006 (TASK-224, implemented):** the JSON logger documents only the fields it emits (level, message, logger, extra, exc_info; no request id, D-7).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-001, SR-008, SR-026, SR-031; SR-042, SR-043 and SR-023 (AC 6, through `U-API-ClientAddress`; AC 7, through the router decisions) were added by CR-004.
Non-functional requirements constraining this item: —.

## Interfaces

Provided and consumed interfaces are specified in
[12-interfaces.md](../../design/12-interfaces.md); the runtime interactions this item takes part in
are in [06-runtime-views.md](../../design/06-runtime-views.md) and the sequence diagrams under
[`../../specifications/`](../../specifications/).

## Architecture narrative

This record is a summary and traceability anchor, not the narrative. The design itself is in the
arc42 sections — [05 building blocks](../../design/05-building-blocks.md) for the decomposition,
[04 solution strategy](../../design/04-solution-strategy.md),
[08 cross-cutting concepts](../../design/08-cross-cutting-concepts.md) and, for deployment,
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0003](../../design/adr/), [ADR-0006](../../design/adr/), [ADR-0008](../../design/adr/), [ADR-0009](../../design/adr/), [ADR-0010](../../design/adr/), [ADR-0011](../../design/adr/), [ADR-0019](../../design/adr/0019-originating-client-address-trusted-proxy-rule.md), [ADR-0021](../../design/adr/0021-bounded-attachment-io-and-bound-two-pass-download.md), [ADR-0022](../../design/adr/0022-blocking-io-off-the-event-loop-with-matched-pools.md).

## Risk relevance

Participates in RISK-001, RISK-005, RISK-007 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): unit changes for the planned design added (marked "CR-004"), links added. Content change, so the approval record is cleared and the record returns to review. The implementing tasks confirm the unit text when they land.
- 1.2 (2026-11-08) — TASK-201 (CR-004): unit text replaced with the unit as built (`U-API-ClientAddress`, `U-API-RateLimit`, `U-API-Security`); router actions and `requires_admin_projection` added to `U-API-Routers`; the 503 and 400 problems added to `U-API-ErrorHandler`. Arc42 sections 05, 06, 08 and 12 updated. Content change, so the 1.1 approval record is cleared and the record returns to review.
- 1.3 (2026-11-13) — CR-006 Plan stage (Software Architect role): planned units for blocking IO off the event loop and pool sizing (ADR-0022), the upload body guard (ADR-0021) and the logger field list (D-7), marked "CR-006 (planned)". Content change, so the 1.2 approval record is cleared and the record returns to review; the implementing tasks confirm the text when they land.
- 1.4 (2026-11-13) — TASK-227 (CR-006, ADR-0023): `U-API-Routers` and `U-API-Deps` use the `DbSession` alias (scope `function`). Content change, so the 1.3 approval record is cleared and the record returns to review.
- 1.5 (2026-11-14) — TASK-225 (Document Writer): the "CR-006 (planned)" markers for blocking IO off the event loop (TASK-136), the upload body guard (TASK-135) and the logger field list (TASK-224) are removed: the units are implemented as described (the guard is `AttachmentBodyLimitMiddleware`, `backend/app/core/body_limit.py`). Wording only. Content change on an approved record, so the 1.4 approval record is cleared and the record returns to review.
