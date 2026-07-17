---
id: "TASK-149"
type: task
title: "Design-token theme foundation with light/dark colorSchemes"
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
  - target: "TASK-081"
    relation: relates_to
tags: ["phase:ui-enhancement"]
---

- **Software item / unit:** SI-FE-SHELL / U-FE-Theme
- **Implements:** SR-037 (AC-1 centralized token definition), SR-038 (AC-1 two value sets over one token structure, AC-3 AA-verified palette)
- **Depends on:** none (first task of the series); TASK-150…153 build on this
- **Specification:** ADD-001 (all token values), ADR-0014 (mechanism)

## Objective

Rebuild `frontend/src/core/theme/theme.ts` as the single MedHub design-token definition using MUI v9 `createTheme` with `cssVariables: { colorSchemeSelector: "data" }` and `colorSchemes: { light, dark }`, carrying exactly the palettes, typography, radius, shadow, and spacing values specified in ADD-001. Self-host the fonts. No visual redesign of individual components yet (that is TASK-150) — this task establishes the token source of truth and must leave the app rendering correctly in light mode.

## Files to modify

- `frontend/src/core/theme/theme.ts` — replace single-mode theme with `colorSchemes` light/dark palettes (ADD-001 §2), typography scale with Manrope headings + Inter body and `"tnum"` for tabular data (§3), `shape.borderRadius: 12`, custom `shadows[1..4]` per scheme (§4); keep 8px spacing and the ≥44px `MuiButtonBase`/`MuiIconButton` touch-target overrides (TASK-081 regression guard). Export a shared constant for the color-scheme attribute/storage key (used by TASK-151's inline script).
- `frontend/src/core/theme/ThemeProvider.tsx` — keep API (`children` only); pass `defaultMode="system"` and enable `CssBaseline` with `enableColorScheme`.
- `frontend/src/main.tsx` (or `App.tsx` import site) — add `@fontsource-variable/manrope` and `@fontsource-variable/inter` imports.
- `frontend/package.json` — add the two Fontsource packages (no other new deps, no CDN).

## Verification

- `frontend/src/core/theme/theme.test.ts` extended: both `theme.colorSchemes.light` and `.dark` exist and define `background.default/paper`, `text.primary/secondary`, `primary.main`, and all four status colors with the exact ADD-001 hex values; touch-target and spacing tests still pass unchanged.
- App boots (`npm run dev`) with no console errors; light rendering shows new fonts/background; `tsc` + eslint + full vitest suite pass (SR-037 AC-5 no functional regression).

## Risks

- Existing tests or code reading `theme.palette.*` as literal strings may break under CSS variables — fix call sites to `theme.colorSchemes.*`/`theme.vars.*`, do not weaken assertions.
- Font bundle size: variable fonts only, two families, no static weight packages.
