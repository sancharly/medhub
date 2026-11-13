---
id: "PRB-013"
type: problem-report
title: "Task enqueue failures are swallowed without a log"
status: open
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-13"
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

## Investigation

Narrowed on 2026-11-13 (CR-006 D-1, D-5). All three enqueue sites now log one WARNING with an id and no personal data, and keep best-effort behaviour: `identity/lifecycle.py:73-76` (session kill; synchronous invalidation already done), `appointments/service.py:73-75` (notification, also shown in the application, SR-035 AC 3) and `identity/erasure.py:141-142` (erasure code e-mail, which version 1.1 listed as unlogged). **Remaining gap:** the retrieval code exists nowhere else, so when its e-mail cannot be queued the data subject has no recovery path and the request still reports success (SR-024 AC 1). Decision D-5: that one request fails with a retryable error; activation and appointment paths stay best effort with the WARNING log.

## Resolution

Partly addressed by TASK-207 (logging at the three sites). The remaining gap, failing the erasure request when the code e-mail cannot be queued, is carried by TASK-141 (draft) under CR-006. **Stays `open`.**

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding I.

## Version history

- 1.0 (2026-09-17) — Created from the July 2026 code review. `open`.
- 1.1 (2026-11-07) — TASK-207: current line numbers; the two call sites now logged; what remains open listed. Stays `open`.
- 1.2 (2026-11-13) — CR-006: Investigation added; scope narrowed to the erasure request (D-5). Stays `open`.
