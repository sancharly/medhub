---
id: "TASK-151"
type: task
title: "Theme-mode toggle, system default, persistence, no-flash init"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-17"
updated: "2026-07-17"
links:
  - target: "SR-039"
    relation: implements
  - target: "SR-038"
    relation: implements
  - target: "TASK-149"
    relation: relates_to
tags: ["phase:ui-enhancement"]
---

- **Software item / unit:** SI-FE-SHELL / U-FE-Theme + U-FE-Layout
- **Implements:** SR-039 (all AC), SR-038 (dark mode reachable everywhere)
- **Depends on:** TASK-149 (colorSchemes theme) — must be merged first; independent of TASK-150

## Objective

Give users the mode control: a permanently visible, accessible toggle in the app chrome header that switches light/dark instantly via MUI `useColorScheme()`; system-preference default until an explicit choice; explicit choice persisted client-side; no flash of the wrong theme on load. Purely presentational — no backend/API change, nothing but the mode string in `localStorage` (SR-039 AC-6).

## Files to modify

- `frontend/src/core/layout/AppLayout.tsx` (header region) — mount the toggle in the chrome so it appears on every screen that shows the chrome (SR-039 AC-1); pre-auth screens without chrome still receive the resolved mode from the provider (AC-5).
- `frontend/src/core/theme/ModeToggle.tsx` (new) — `IconButton` using `useColorScheme()`: shows sun/moon per resolved mode, `aria-label` describing the action (e.g. "Switch to dark mode"), keyboard operable, ≥44px target. Explicit activation calls `setMode("light"|"dark")`; while mode is `system`, follows OS changes live (AC-3).
- `frontend/index.html` — inline pre-hydration script: read the stored mode key (shared constant from TASK-149; `system`/absent → `matchMedia("(prefers-color-scheme: dark)")`), set the color-scheme `data-` attribute on `<html>` and a matching `background-color` (`#F4F7F6` / `#0E1413`) before the bundle loads — prevents flash-of-wrong-theme.

## Verification

- Component tests (`ModeToggle.test.tsx`): toggle renders with accessible name; click switches `<html>` scheme attribute without remounting a sibling holding form state (assert an input keeps its typed value across a toggle — SR-039 AC-2); mode persists to `localStorage` and is restored on re-render of the provider (AC-4); with no stored value and mocked `matchMedia` dark, app resolves dark (AC-3).
- Manual: toggle visible on all chrome screens at phone/desktop widths; reload in dark mode shows no light flash; login (pre-auth) respects the mode (AC-5).
- Full suite + `tsc` + eslint green.

## Risks

- Inline script and theme constant drifting apart → single exported constant, plus a test asserting `index.html` contains the same key/attribute string.
- Flash on slow devices if the script sits after CSS links — keep it first in `<head>`.
