---
id: "PRB-032"
type: problem-report
title: "JSON log formatter drops the request-id field it promises"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-14"
criticality: minor
links: []
tags: ["correctness"]
---

# PRB-032 — JSON log formatter drops the request-id field it promises

## Observed

`app/core/logging.py` documents a `request-id` field that the formatter never emits.

## Impact

Log correlation across a request is impossible, which slows incident analysis (SR-023 adjacent, not part of the audit trail itself).

## Safety evaluation

Contributes weakly to RISK-006 (detectability).

## Resolution

Resolved in CR-006 by TASK-224 (D-7: the promise is dropped, the field is not implemented). The formatter
never emitted a request id and no `request_id` exists in `backend/app`. The `core/logging.py` module docstring now
lists the fields the formatter emits (`level`, `message`, `logger`, `extra`, `exc_info`) and no others. The only text promising the field was the TASK-002 logging bullet, which no longer does
(TASK-002 1.1). Log output is unchanged. Verify: `grep -rn -i "request.id\|request_id" backend/app docs/design`
finds nothing, and `cd backend && uv run pytest tests/test_log_redaction.py tests/workers/test_email_tasks_logging.py`
passes (TS-017).

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Simplicity / hygiene.
