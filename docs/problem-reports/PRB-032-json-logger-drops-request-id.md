---
id: "PRB-032"
type: problem-report
title: "JSON log formatter drops the request-id field it promises"
status: open
criticality: minor
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
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

Not yet tracked by a task. Proposed: emit the request id from the middleware context, or drop the promise from the docstring. Needs a task and a CR.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Simplicity / hygiene.
