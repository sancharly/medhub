---
id: "PRB-060"
type: problem-report
title: "An allowed authorization decision leaves no audit row when the request then fails"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
criticality: minor
links:
  - target: "SR-023"
    relation: relates_to
  - target: "RISK-006"
    relation: relates_to
  - target: "PRB-058"
    relation: relates_to
tags: ["audit", "authz", "backend"]
---

# PRB-060 — An allowed authorization decision leaves no audit row when the request then fails

## Observed

Found by QA in the TASK-187 review (round 1, 2026-10-31). An `AUTHZ_ALLOWED` row (outcome SUCCESS)
is added to the request transaction (ADR-0016). When the handler then raises, `get_db` rolls the
request session back and the row is lost.

Reproduction (real PostgreSQL, `create_app()`): mount a module router behind an enabled module
gate whose route raises `ValidationProblem`. The response is `400` and `audit_log` holds **zero**
rows for the actor, although the module access decision was allowed. Pinned by
`backend/tests/audit/test_authz_decision_audit.py::test_allowed_row_is_lost_when_the_handler_then_fails_prb_060`.

Reachable in production: the DICOM module (`backend/modules/dicom_viewer/dicom_viewer/router.py:54-55`,
frame out of range or wrong content type, `400`) and the `502` checksum path. The attachment was
read and both the module and the clinical decisions were allowed, yet neither is audited. The
clinical `AUTHZ_ALLOWED` row has the same loss and existed before CR-004; the module row (TASK-187)
adds a second case.

## Impact

SR-023 AC 7 says no allowed or denied access is decided without an entry. For a request that ends
in an error, the allowed decision has none. Access that was granted is then absent from the
trail (RISK-006, audit completeness). Denials are not affected: `AUTHZ_DENIED` is FAILURE and
is written on its own transaction.

## Investigation

- `AuthorizationService.authorize` records `AUTHZ_ALLOWED` (`backend/app/authz/service.py:87`);
  `AuditService.record` makes only FAILURE rows and `_INDEPENDENT_ACTIONS`
  (`backend/app/audit/service.py:20`, only `ACCOUNT_LOCKOUT`) independent; everything else joins the
  request transaction.
- `get_db` rolls back on any exception (`backend/app/db/repositories/session.py:28-32`).
- Fix options: add `AUTHZ_ALLOWED` to `_INDEPENDENT_ACTIONS` (an ADR-0016 amendment). Every allowed
  decision would then take a second pooled connection. PRB-058 shows that the independent write
  waits on the shared pool and is lost when the pool is exhausted, so doing this first would turn
  that exhaustion into a normal-load problem (one extra connection per request, several per DICOM
  frame request). The fix therefore waits for PRB-058 (a dedicated audit pool).

## Safety evaluation

No direct patient harm: access decisions are correct, only the evidence of a granted access on a
failed request is missing. The request failed, so no data was returned in the `400` path; on the
`502` path the data was not delivered either. Hence `minor`. No released version exists, so no
notification is needed. It must be resolved, or evaluated as a residual anomaly, before the first
release. RISK-006 "Risks introduced by controls" needs a note for this PRB (to be added by the
human in a later task).

## Proposed resolution

After PRB-058 gives the audit write its own pool: record `AUTHZ_ALLOWED` independently (amend
ADR-0016), flip the pinning test to expect one row, and re-measure the DICOM frame path (SR-026).

## Source

QA, TASK-187 review round 1 (2026-10-31).
