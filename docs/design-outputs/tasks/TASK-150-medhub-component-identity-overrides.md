---
id: "TASK-150"
type: task
title: "MedHub component identity via theme styleOverrides and status pills"
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
  - target: "TASK-149"
    relation: relates_to
tags: ["phase:ui-enhancement"]
---

- **Software item / unit:** SI-FE-SHELL / U-FE-Theme
- **Implements:** SR-037 (AC-2 components consume tokens, AC-3 equivalent elements styled identically, AC-4 professional/modern/elegant identity), SR-038 (AC-4 status distinguishable, not color-alone)
- **Depends on:** TASK-149 (token foundation) — must be merged first

## Objective

Express the MedHub identity ("Clinical Calm", ADD-001 §1) globally through `theme.components` styleOverrides so every screen inherits it without per-screen changes: elevated cards on the soft page background, generous radii, soft shadows (borders in dark mode), restrained chrome, tinted status pills with icons, elegant data tables. All styling flows from ADD-001 tokens — no new hex values outside the theme.

## Files to modify

- `frontend/src/core/theme/theme.ts` — add styleOverrides/defaultProps for: `MuiPaper`/`MuiCard` (radius 16, shadow level 2, 1px `border.subtle`, dark-mode border emphasis), `MuiAppBar`/`MuiDrawer` (neutral surfaces, active-item `bg.selected` + `primary.onSelected`), `MuiButton` (radius 12, no uppercase, contained=primary with verified contrast text), `MuiTextField`/`MuiOutlinedInput` (radius 8, `border.input` outline, visible focus ring in accent), `MuiTableHead`/`MuiTableRow` (subtle header bg, row hover, tabular numerals), `MuiChip`, `MuiDialog` (radius 16, shadow level 4, 40–60% scrim), `MuiAlert` (pill tint sets), `MuiTabs`, `MuiTooltip`. Disabled states at reduced emphasis, never invisible.
- `frontend/src/core/theme/StatusPill.tsx` (new) — shared status-pill component: pill radius, tint background + tinted text + **leading icon per severity** (success/warning/error/info from ADD-001 pill sets), so state is never conveyed by color alone (SR-038 AC-4). Export from `frontend/src/core/theme/index.ts` (create if absent).
- Icon-badge pattern (list/table leading icons on `bg.selected`/secondary tints) as a small styled helper in the same module if the sweep (TASK-152) needs it.

## Verification

- Component tests: `StatusPill` renders icon + label per severity in both schemes; buttons/inputs expose focus-visible outline; Chip/Alert severity colors resolve to ADD-001 values.
- Visual pass of representative screens (patients list, appointments, admin accounts, login) in light mode: identical treatment of equivalent elements (SR-037 AC-3).
- `tsc`, eslint, full vitest suite green; no screen-level code changed in this task.

## Risks

- Over-styling harms clarity: keep chrome quiet, one accent; design review against SR-037 AC-4 before merge.
- Global overrides can shift layout (padding/height) on dense screens — spot-check tables and dialogs at phone width (SR-020 no horizontal scroll).
