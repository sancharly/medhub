---
id: "PRB-025"
type: problem-report
title: "Idle timer resets on every mouse and scroll event"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-14"
criticality: minor
links: []
tags: ["performance"]
---

# PRB-025 — Idle timer resets on every mouse and scroll event

## Observed

`frontend/src/auth/useIdleTimer.ts:66` re-arms its timers on every `mousemove` and `scroll` event with no debounce.

## Impact

Wasted main-thread work on long clinical lists; marginal against SR-026.

## Safety evaluation

No hazard: the idle behaviour itself is correct, only inefficient.

## Resolution

Fixed in CR-006 by TASK-222 (D-33) by removing the cause: `frontend/src/auth/useIdleTimer.ts` no longer registers any listener for `mousemove`, `keydown`, `click`, `touchstart` or `scroll`, and has no activity-driven re-arm. Input events therefore do no session-timer work, which meets SR-026 AC 8 with zero re-arms (the debounce proposed here is superseded; its wording is left to the human, CR-006 P-20). The client deadline is re-armed only by a new server-derived deadline (`me`, extend), see PRB-087.

Tests: `useIdleTimer.test.ts` `no listeners registered for activity events` and `activity events do not move the deadline` (TS-018 TC-018.9).

Verified 2026-11-14 in the working tree: `npm test -- --run` (35 files, 361 tests), `npm run typecheck`, `npm run lint`, `npm run build` clean; the six negative controls of TASK-222 each fail at least one test (TS-001 TC-001.13). Not yet confirmed through a shipped release, so the status is `resolved`, not `closed`.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Performance.
