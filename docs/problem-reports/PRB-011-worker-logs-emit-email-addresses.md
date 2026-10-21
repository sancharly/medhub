---
id: "PRB-011"
type: problem-report
title: "Worker logs emit email addresses, bypassing audit scrubbing"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
criticality: major
links: []
tags: ["privacy", "hazard:privacy"]
---

# PRB-011 — Worker logs emit email addresses, bypassing audit scrubbing

## Observed

`workers/email_tasks.py:170` logs the recipient address in a structured `extra` field. `AuditService` scrubbing protects audit rows only, so the JSON stdout stream carries raw PII to whatever log sink collects it.

## Impact

An uncontrolled copy of personal data outside the retention and erasure machinery (SR-024, NFR-004): erasure cannot reach log archives.

## Safety evaluation

Contributes to RISK-008 (personal data retained, copied or erased contrary to its lawful basis).

## Resolution

TASK-138 (draft) — scrub or hash PII in worker and notification logs and add a test asserting no address reaches the log stream.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding E.
