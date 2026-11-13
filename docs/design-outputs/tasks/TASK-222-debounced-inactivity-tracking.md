---
id: "TASK-222"
type: task
title: "Inactivity tracking re-arms its timers at most once per second"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-13"
links:
  - target: "SR-026"
    relation: implements
  - target: "SR-030"
    relation: implements
  - target: "RISK-005"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-025"
    relation: relates_to
  - target: "ADD-019"
    relation: relates_to
  - target: "TASK-144"
    relation: relates_to
tags: ["cr:CR-006", "frontend", "session", "control:design"]
---

# TASK-222 — Inactivity tracking re-arms its timers at most once per second

- **Software item / unit:** SI-FE-AUTH `auth/useIdleTimer.ts` (ADD-019).
- **PRB:** PRB-025. **CR:** CR-006 (change-analysis cause 10).
- **Depends on:** TASK-144 (same provider; commit after it).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** XS (`frontend/src/auth/useIdleTimer.ts` and its test; records TS-018, TS-001).

## Objective

SR-026 AC 8: the inactivity tracking re-arms its timers at most once per second of continuous activity, and the
SR-030 AC 1 and AC 2 deadlines stay accurate to within that second. `useIdleTimer` calls `resetDeadline` on
every mouse, scroll and key event. Server enforcement is unchanged (RISK-005 not raised).

## Implementation detail

- Leading-edge throttle: the first event re-arms immediately; further events within 1 000 ms only set a
  "pending" flag, honoured at the end of the window (trailing re-arm), so the deadline differs from
  "last activity + timeout" by at most 1 s. No library; a timestamp and one timer.

## Tests (write first)

- `re-arms at most once per second under continuous events` (SR-026 AC 8): 100 events over 1 s → ≤ 2 re-arms.
- `deadline accurate within one second` (SR-026 AC 8; SR-030 AC 1, AC 2): last event at t, warning at
  deadline − 2 min ± 1 s.
- Existing `useIdleTimer` tests unchanged.
- TS-018 TC-018.7; TS-001 note.

## Acceptance criteria

- [ ] SR-026 AC 8; SR-030 AC 1, AC 2, AC 4 timings within 1 s.

## Definition of Done

- [ ] Frontend lint, type check, suite green; `traceability-check` no error for this record

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect) for PRB-025.
