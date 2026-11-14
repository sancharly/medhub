---
id: "PRB-013"
type: problem-report
title: "Task enqueue failures are swallowed without a log"
status: resolved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-14"
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

TASK-207 logs the session-kill and appointment-notification enqueue failures (best effort kept, D-5). TASK-141 (CR-006, SR-024 AC 6) closes the remaining gap: `identity/erasure.py` enqueues the retrieval-code e-mail before the sessions are invalidated and, if it cannot be queued, logs one WARNING with the dataset id and raises `ErasureNotificationUnavailableProblem` (503, `Retry-After`), so the request transaction rolls back and the account, its PII and its sessions stay unchanged. Verified by TS-004 TC-004.4 and TS-017 TC-017.7.

QA verification (TASK-141 round 1, 2026-11-14): `test_erasure_enqueue_failure_rolls_back_and_returns_503` (real `create_app()` and PostgreSQL) and the two unit tests pass; with the `raise` replaced by `pass` (scratch copy) all three fail. Residual noted as TASK-141 QA LOW 1: if the commit fails after the enqueue, a misleading e-mail can be sent (no data loss). Backend suite 1670 passed, `mypy` and `ruff check` clean. Fixed and verified in the working tree, so `resolved`; `closed` once confirmed through a shipped release.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding I.

## Version history

- 1.0 (2026-09-17) — Created from the July 2026 code review. `open`.
- 1.1 (2026-11-07) — TASK-207: current line numbers; the two call sites now logged; what remains open listed. Stays `open`.
- 1.2 (2026-11-13) — CR-006: Investigation added; scope narrowed to the erasure request (D-5). Stays `open`.
- 1.3 (2026-11-14) — QA review of TASK-141 (round 1): APPROVED; Resolution names the fix and its evidence; `open → resolved` (CR-006 holds the `resolves` link).
