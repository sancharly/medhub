---
id: "PRB-025"
type: problem-report
title: "Idle timer resets on every mouse and scroll event"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
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

Not yet tracked by a task. Proposed: debounce the activity handler. Needs a task and a CR.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Performance.
