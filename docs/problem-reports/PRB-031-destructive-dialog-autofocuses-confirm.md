---
id: PRB-031
type: problem-report
title: Destructive confirmation dialog focuses Confirm instead of Cancel
status: rejected
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-15"
criticality: minor
links: []
tags:
  - usability
  - hazard:data-integrity
---

# PRB-031 — Destructive confirmation dialog focuses Confirm instead of Cancel

## Observed

`frontend/src/core/.../ConfirmDialog.tsx:51` sets `autoFocus` on the Confirm button even when the dialog is marked `destructive`, so Enter confirms a destructive action.

## Impact

A keyboard user can delete or deactivate by pressing Enter (SR-027 usability controls, SR-034 account deletion).

## Safety evaluation

Contributes to RISK-008 (data erased when it should not be) in the mildest form: the action is still audited and, for accounts, recoverable per ADR-0013.

## Resolution

Rejected: already fixed before CR-006, working tree verified 2026-11-13 (CR-006 D-1) and again on the branch head on 2026-11-15 (TASK-226). Evidence: `frontend/src/core/confirm/ConfirmDialog.tsx:46` gives the Cancel button `autoFocus={destructive}` and `:51` gives the Confirm button `autoFocus={!destructive}`, so a destructive dialog opens with focus on Cancel and Enter does not confirm. Test: `frontend/src/core/confirm/ConfirmDialog.test.tsx:120`, "destructive variant autofocuses Cancel, not Confirm" (asserts `document.activeElement` is the Cancel button); it passed in the TASK-226 frontend run (412 tests, 41 files). The change came with the phase-6 audit remediations (commit 24240f8, 2026-06-30). No task is needed: SR-027 AC 5 holds as implemented.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Low.

## Version history

- 1.0 (2026-09-17) — Created from the audit findings. `open`.
- 1.1 (2026-11-15) — TASK-226: Resolution replaced by the rejection evidence (CR-006 D-1). Stays `rejected`.
