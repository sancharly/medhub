---
id: "PRB-032"
type: problem-report
title: "JSON log formatter drops the request-id field it promises"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-15"
criticality: minor
links: []
tags: ["correctness"]
---

# PRB-032 — JSON log formatter drops the request-id field it promises

## Observed

The 2026-07 review reported that the JSON log formatter promises a `request-id` field that it never emits. The formatter never emitted one, but `app/core/logging.py` did not document one either (checked at TASK-224): the only text that promised the field was the logging bullet of TASK-002. The defect is a promise in a record, not a missing field in the code.

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
