---
id: "PRB-031"
type: problem-report
title: "Destructive confirmation dialog focuses Confirm instead of Cancel"
status: open
criticality: minor
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["usability", "hazard:data-integrity"]
---

# PRB-031 — Destructive confirmation dialog focuses Confirm instead of Cancel

## Observed

`frontend/src/core/.../ConfirmDialog.tsx:51` sets `autoFocus` on the Confirm button even when the dialog is marked `destructive`, so Enter confirms a destructive action.

## Impact

A keyboard user can delete or deactivate by pressing Enter (SR-027 usability controls, SR-034 account deletion).

## Safety evaluation

Contributes to RISK-008 (data erased when it should not be) in the mildest form: the action is still audited and, for accounts, recoverable per ADR-0013.

## Resolution

Not yet tracked by a task. Proposed: focus Cancel when `destructive` is set, with a test. Needs a task and a CR.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Low.
