---
id: "TASK-152"
type: task
title: "Screen sweep: tokenize ad-hoc styles, verify every screen in both modes"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-17"
updated: "2026-07-17"
links:
  - target: "SR-037"
    relation: implements
  - target: "SR-038"
    relation: implements
  - target: "TASK-150"
    relation: relates_to
  - target: "TASK-151"
    relation: relates_to
tags: ["phase:ui-enhancement"]
---

- **Software item / unit:** SI-FE-CORE (all screen units)
- **Implements:** SR-037 (AC-2 no ad-hoc hard-coded values, AC-3 full-coverage visual review), SR-038 (AC-2 every screen/state fully styled in both modes, AC-5 responsive in both modes)
- **Depends on:** TASK-150 (component identity) and TASK-151 (toggle, to review dark mode) — must be merged first

## Objective

Make token coverage total. Sweep every screen under `frontend/src/core/{layout,nav,patients,appointments,clinical,admin,profile,consent,confirm,error}`, `frontend/src/auth`, `frontend/src/modules`, and `frontend/src/app` for hard-coded colors, radii, shadows, and font values in `sx`/`styled`/inline styles; replace with theme token references or delete where the TASK-150 overrides already provide the styling. Then review every screen in **both** modes and fix anything unthemed.

## Approach

1. Inventory: grep the frontend `src` for `#[0-9a-fA-F]{3,8}`, `rgb(`, `rgba(`, `boxShadow:`, `fontFamily:`, `grey[`, `common.white/black` outside `core/theme/`; each hit is either migrated to a token reference or justified in the PR description (e.g. DICOM canvas internals).
2. Surgical changes only: replace values, do not restructure components (CLAUDE.md §3).
3. Two-mode review checklist (SR-038 AC-2): every screen, dialog, menu, toast, empty/loading/error state, hover/focus/disabled state — no unthemed surface, invisible text, or residual light-mode colors in dark mode; checked at phone/tablet/desktop widths (AC-5). Record the checklist in the PR.

## Verification

- Inventory grep returns zero unjustified hits outside `core/theme/`.
- Two-mode, three-breakpoint visual review checklist completed for every screen (attach to PR — this is the SR-037 AC-3 / SR-038 AC-2 evidence).
- Full vitest suite green; no behavioral diffs (SR-037 AC-5): navigation, forms, and dialogs work identically.

## Risks

- Highest-regression task of the series (touches many files): keep commits per-module, review diffs against "styling-only" expectation.
- Dark-mode gaps hide in rarely-visited states (error boundaries, idle-warning dialog, activation flow) — the checklist enumerates them explicitly.
- Snapshot/DOM assertions on colors or class names may fail — update assertions to token references, never hard-code new hex in tests.
