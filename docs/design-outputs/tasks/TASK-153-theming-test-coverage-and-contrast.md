---
id: "TASK-153"
type: task
title: "Theming test coverage: tokens, contrast, toggle, persistence, system default"
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
  - target: "SR-039"
    relation: implements
  - target: "TASK-152"
    relation: relates_to
tags: ["phase:ui-enhancement"]
---

- **Software item / unit:** SI-FE-SHELL / U-FE-Theme (tests)
- **Implements:** SR-037 AC-1/AC-5, SR-038 AC-1/AC-3, SR-039 AC-1…AC-4 (automated verification)
- **Depends on:** TASK-149/150/151 merged; runs after TASK-152 to lock the final state

## Objective

Consolidate automated coverage for the theming system in the existing vitest + Testing Library setup so future token or component changes cannot silently regress contrast, persistence, or mode behavior. Each test names the SR/AC it verifies (project convention, TASK-081).

## Files to modify

- `frontend/src/core/theme/theme.test.ts` — extend:
  - both colorSchemes define the full ADD-001 token set; light and dark expose the **same token structure** (same key paths — SR-038 AC-1).
  - **Automated WCAG contrast test:** implement the WCAG 2.1 relative-luminance ratio in the test file and assert every essential pair from ADD-001 §6 (text/surface, button, pill text/bg, input outline, focus ring — both schemes) meets its 4.5:1 or 3:1 threshold (SR-038 AC-3). Token edits then fail CI when contrast breaks.
  - touch-target ≥44px and 8px spacing tests retained (TASK-081 guard).
- `frontend/src/core/theme/ModeToggle.test.tsx` — (from TASK-151, extend as needed): accessible name + keyboard activation (SR-039 AC-1); switch without losing sibling form input (AC-2); explicit choice persisted and restored across provider remount, and it overrides a conflicting mocked `matchMedia` system preference (AC-4); no stored choice → follows mocked system preference, including a `change` event while mode is `system` (AC-3).
- `frontend/src/core/theme/StatusPill.test.tsx` — each severity renders a distinct icon + label in both schemes (SR-038 AC-4 non-color-only).
- `frontend/index.html` sync test — the inline script uses the same storage key and attribute name as the exported theme constant (guards ADR-0014 negative consequence).

## Verification

- All new tests pass; full frontend suite (`npm test`), `tsc`, eslint green — SR-037 AC-5 regression evidence.
- Coverage: `frontend/src/core/theme/` fully covered by unit/component tests; test names cite SR/AC.

## Risks

- jsdom has no real `matchMedia`/CSS-variable resolution: mock `matchMedia` (existing test-setup pattern) and assert on theme objects/attributes rather than computed pixel colors.
- Contrast test must import token values from `theme.ts` (single source), not duplicate hex literals — otherwise the test can pass while the theme drifts.
