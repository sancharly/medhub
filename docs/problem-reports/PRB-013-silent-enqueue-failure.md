---
id: "PRB-013"
type: problem-report
title: "Task enqueue failures are swallowed without a log"
status: open
criticality: major
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["correctness", "hazard:denial-of-care"]
---

# PRB-013 — Task enqueue failures are swallowed without a log

## Observed

`identity/lifecycle.py:57` and `appointments/service.py:71` wrap `.delay()` in `except Exception: pass` with no logging, so a dead broker silently drops session-kill propagation and appointment notifications.

## Impact

SR-035 notifications and session revocation can fail with no operational signal at all.

## Safety evaluation

Contributes to RISK-009 (notification not delivered) and RISK-005 (a session that should have been killed stays alive).

## Resolution

TASK-141 (draft) — log and surface enqueue failures, and fail the request where the side effect is security-relevant.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding I.
