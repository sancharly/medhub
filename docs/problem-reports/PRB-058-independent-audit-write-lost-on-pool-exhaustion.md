---
id: "PRB-058"
type: problem-report
title: "Independent audit write waits on the shared connection pool and is lost when the pool is exhausted"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
criticality: minor
links: []
tags: ["audit", "security", "backend"]
---

# PRB-058 — Independent audit write waits on the shared connection pool and is lost when the pool is exhausted

## Observed

Found by QA while reviewing CR-002 TASK-183 (commit `8473fbe`) on 2026-10-30. QA set the engine to
`pool_size=1, max_overflow=0, pool_timeout=2` and sent a request down the `AUTHZ_DENIED` path.
After 2.1 s the response was a generic `500` instead of `403`, and `audit_log` had no row for the
denial. The exception appears only in the server log.

## Impact

Under connection-pool exhaustion, the failure and refusal events that ADR-0016 meant to protect
(`AUTHZ_DENIED`, `LOGIN_FAILURE`, `ACCOUNT_LOCKOUT`, `ACTIVATION_FAILED`, the `DICOM_STUDY_READ`
and `ATTACHMENT_ACCESS` FAILUREs) are lost, and the client gets a `500` after `pool_timeout`.
The likeliest trigger is a burst of failed requests, such as credential spraying. That is exactly
when this evidence matters most. SR-023 AC 1 and AC 2 are not met under that load.

## Investigation

- `AuditRepository.add_independent` (`backend/app/db/repositories/audit_repo.py:23-32`) opens
  `Session(bind=self._session.get_bind())`. That draws a **second** connection from the same pool
  while the request session (`get_db`, `backend/app/db/repositories/session.py:22-32`) still holds
  its first one.
- The engine (`backend/app/db/repositories/session.py:14-16`) uses SQLAlchemy's default pool:
  5 + 10 overflow, `pool_timeout` 30 s. If 15 concurrent requests each hold one connection and
  each needs a second, they all wait. Each one fails after 30 s, and no row is written.
- The burst is not bounded. The per-account lockout (`backend/app/auth/lockout.py:60-88`) counts
  failures per account and per email. A spray of distinct unknown emails
  (`backend/app/auth/login.py:80-92`) never reaches a threshold, and login has no rate limit.
- The record claims made at the CR-002 PRB-052 amendment were wrong: "the row is not silently
  dropped" and "the Redis lockout limits the burst" (RISK-006 1.2, the CR-002 §7.4 row for
  TASK-183, and ADR-0016 "Consequences"). RISK-006 and CR-002 are corrected in CR-002 1.8.

## Safety evaluation

There is no direct patient harm. Access is still denied, so the `500` reveals no data and changes
none. The defect is a partial failure of a RISK-006 control (severity 2) under abnormal load. It
needs a burst that exhausts the pool. Normal load and the CR-002 tests are unaffected. Hence
`minor`. No released version exists (no `docs/releases/`, no git tag), so no notification is
needed. It must be resolved, or evaluated as a residual anomaly, before the first release.

## Proposed resolution

- Give `add_independent` its own cached audit engine, separate from the request pool. It should
  have a small dedicated pool (for example `pool_size=2, max_overflow=3`) and a short
  `pool_timeout` (for example 2 s), so that an audit write never waits on connections held by
  requests that are themselves waiting.
- Decide whether a write that still fails should go to a durable fallback, for example a
  structured log line with the full event, so that it is not lost silently.
- Consider login rate limiting per source IP, so a spray of unknown emails is bounded.
- Add a real-database test: with the request pool exhausted, a denial still writes its row.
- Correct the "Cost" bullet of ADR-0016.

Needs a task and a CR. It is outside CR-002's scope unless the human decides otherwise.

## Source

QA, CR-002 TASK-183 review (2026-10-30).
