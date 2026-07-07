---
id: "TASK-081"
type: task
title: "Responsive layout + MUI theme"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-020"
    relation: implements
  - target: "NFR-003"
    relation: implements
  - target: "TASK-001"
    relation: relates_to
tags: ["audit-verified", "phase:6-frontend-foundation"]
---

- **Phase:** 6 — Frontend foundation
- **Software item / unit:** SI-FE-SHELL / U-FE-Layout
- **Implements:** SR-020 (AC-1 adapts at phone/tablet/desktop breakpoints with no horizontal scroll of primary content; AC-3 adequate touch targets, no clipped controls); NFR-003 (responsive across desktop/tablet/phone)
- **Depends on:** TASK-001 (monorepo structure, frontend toolchain, Vite) — must be merged first
- **Branch:** `feature/fe-layout-theme`
- **Status:** Completed (audit-verified 2026-06-29)

## Objective

Build the **application shell layout and MUI theme** that every screen renders inside: a responsive app frame (header, navigation slot, main content slot) that reflows across phone, tablet, and desktop breakpoints with **no horizontal scrolling of primary content** (SR-020 AC-1), plus a single MUI theme that fixes typography, spacing, color, and minimum touch-target sizing so controls stay reachable on small screens (SR-020 AC-3, NFR-003). This is the visual foundation the navigation (TASK-082), dialogs (TASK-083), error surface (TASK-084), and all feature views build on. It owns layout structure only — no data fetching, no routes. Traces to SR-020, NFR-003.

## Interfaces to honor

Provides the layout half of `ShellServices` from [12-interfaces.md](../../design/12-interfaces.md) §12.2 (provider SI-FE-SHELL; consumers SI-FE-CORE, modules):

```ts
// layout slots only in this unit; navigation/confirm/error are TASK-082/083/084
interface AppLayoutProps {
  navigation: React.ReactNode;   // filled by TASK-082
  children: React.ReactNode;     // the active route's content
}
```

- Exposes named layout regions (header, navigation, main content) so SI-FE-NAV (TASK-082), the confirm dialog (TASK-083), and the error/toast surface (TASK-084) plug into well-defined slots without re-implementing layout.
- Uses **MUI** responsive primitives and the `theme.breakpoints` for phone/tablet/desktop (ADR-0003 accessible/responsive component library).
- Must **not**: fetch data or own routes (that is TASK-082 + Phase 7); hard-code colors/spacing/fonts outside the central theme; introduce browser-proprietary CSS without a standards-based fallback (cross-browser, SR-019/ADR-0003); allow primary content to overflow horizontally at any supported breakpoint (SR-020 AC-1).

## Implementation detail

- Files to create:
  - `frontend/src/core/theme/theme.ts` — the MUI theme: typography scale, palette, spacing, and a global minimum interactive target size (≥ 44×44 CSS px) so touch targets are adequate on small screens (SR-020 AC-3).
  - `frontend/src/core/theme/ThemeProvider.tsx` — wraps the app in MUI `ThemeProvider` + `CssBaseline` (normalizes cross-browser defaults, ADR-0003).
  - `frontend/src/core/layout/AppLayout.tsx` — the responsive frame: header region, a navigation slot, and a scrollable **main content** region that never scrolls horizontally; uses MUI `Box`/`Grid`/`Container` with `theme.breakpoints`.
  - `frontend/src/core/layout/breakpoints.ts` — the named phone/tablet/desktop breakpoints (single source of truth, reused by TASK-082 nav collapse).
  - `frontend/src/core/layout/index.ts` — exports `AppLayout`, theme provider.
- Libraries (exact stack): React 18, MUI (`ThemeProvider`, `CssBaseline`, `Box`, `Container`, `useMediaQuery`), TypeScript.
- Breakpoints: phone (collapsed nav, single-column content), tablet (intermediate), desktop (persistent nav + wider content). Primary content uses fluid widths and wrapping so it fits the viewport width — verified to produce no horizontal scrollbar (SR-020 AC-1). The DICOM viewer's own canvas sizing is out of scope here (TASK-102).
- Theme enforces adequate target sizing and contrast via the accessible component library baseline (NFR-003, §8.10); full accessibility audit is post-MVP (§8.10).
- This unit renders structure and styling only; navigation content is injected by TASK-082.

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + React Testing Library), `frontend/src/core/layout/AppLayout.test.tsx`:
  - renders header, navigation slot, and main content slot; injected nav and children appear in their regions.
  - at a phone-width viewport (mocked `matchMedia`), the layout uses the single-column/collapsed arrangement; at desktop width, the persistent arrangement (SR-020 AC-1, NFR-003 AC-1).
  - primary content container does not produce horizontal overflow at phone/tablet/desktop widths (SR-020 AC-1) — asserted via computed style / no `scrollWidth > clientWidth`.
- Theme test, `frontend/src/core/theme/theme.test.ts`:
  - interactive components resolve to a minimum target size ≥ 44 px from the theme (SR-020 AC-3).
  - the theme exposes the three named breakpoints used by the nav (TASK-082).
- Each test names the SR/NFR AC it verifies.

## Acceptance criteria

- [x] The layout adapts at defined phone, tablet, and desktop breakpoints (SR-020 AC-1, NFR-003 AC-1).
- [x] Primary content never requires horizontal scrolling at any supported breakpoint (SR-020 AC-1, NFR-003 AC-1).
- [x] Interactive controls meet a minimum touch-target size and are not clipped on small screens (SR-020 AC-3, NFR-003 AC-3).
- [x] A single MUI theme is the source of truth for typography, color, spacing, and target sizing (ADR-0003).
- [x] Header / navigation / main-content slots are exposed for TASK-082/083/084 to fill.

## Definition of Done

- [x] Lint + type-check pass (`eslint`/`tsc`)
- [x] Unit/component tests pass; coverage target met
- [x] Traceability matrix row updated (SR-020, NFR-003 → TASK-081 → tests)

## Audit verdict (2026-06-29)

- **Verdict:** PASS
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- Acceptance criteria verified met; boxes checked.
