---
id: "PRB-013"
type: problem-report
title: "Task enqueue failures are swallowed without a log"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-07"
criticality: major
links: []
tags: ["correctness", "hazard:denial-of-care"]
---

# PRB-013 — Task enqueue failures are swallowed without a log

## Observed

`identity/lifecycle.py:69` and `appointments/service.py:69` wrapped `.delay()` in `except Exception: pass` with no logging, so a dead broker silently drops session-kill propagation and appointment notifications. Since TASK-207 (2026-11-07) both sites write one WARNING with the account or appointment id (best effort kept; the request still succeeds).

## Impact

SR-035 notifications and session revocation can fail with no operational signal at all.

## Safety evaluation

Contributes to RISK-009 (notification not delivered) and RISK-005 (a session that should have been killed stays alive).

## Resolution

Partly addressed by TASK-207: the two call sites above are logged. **Stays `open`.** What remains: `identity/erasure.py:140` (the retrieval code exists nowhere else, so its loss has no recovery), surfacing failures beyond a log line, and failing the request where the side effect is security-relevant: TASK-141 (draft).

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding I.

## Version history

- 1.0 (2026-09-17) — Created from the July 2026 code review. `open`.
- 1.1 (2026-11-07) — TASK-207: current line numbers; the two call sites now logged; what remains open listed. Stays `open`.
