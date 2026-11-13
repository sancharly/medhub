---
id: "TASK-224"
type: task
title: "Remove the request-id promise from the JSON logger documentation"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-13"
links:
  - target: "SR-043"
    relation: implements
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-032"
    relation: relates_to
  - target: "RISK-006"
    relation: relates_to
  - target: "ADD-005"
    relation: relates_to
tags: ["cr:CR-006", "documentation", "logging"]
---

# TASK-224 — Remove the request-id promise from the JSON logger documentation

- **Software item / unit:** SI-API `core/logging.py` (ADD-005); documentation only.
- **PRB:** PRB-032. **CR:** CR-006 (D-7: drop the promise; no SR, no new field).
- **Depends on:** none (parallel).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** XS (`backend/app/core/logging.py` docstring; arc42 text that repeats the promise, if any, via
  TASK-225).

## Objective

The JSON logger's docstring promises a request-id field that it never emits; no `request_id` exists in
`backend/app`. D-7: the promise is removed rather than implemented. The logger's documented field list then
matches what it emits, which is what SR-043 (log content) relies on. No RISK-006 control relied on the field.

## Implementation detail

- Remove the request-id sentence from the docstring; list the fields actually emitted.
- `grep -rn -i "request.id\|request_id" backend/app docs/design` and remove any other promise of the field
  (docs through TASK-225).

## Tests

- None new (no behaviour change). The existing log-format tests (TS-017) must pass unchanged; QA checks with the
  grep above that no promise remains.

## Acceptance criteria

- [ ] No code or design text promises a request-id field; log output unchanged.

## Definition of Done

- [ ] `ruff`, backend suite green; `traceability-check` no error for this record

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect) for PRB-032 (D-7).
