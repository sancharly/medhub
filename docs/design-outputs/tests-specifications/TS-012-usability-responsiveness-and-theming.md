---
id: TS-012
type: test-specification
title: Usability, responsiveness and theming verification
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: b86b609c1e8617d7fb4f6f6a1b94dc40ee44c5dc370d2adb4cd5c5981be65031
approval_note: self-approved
links:
  - target: SR-019
    relation: verifies
  - target: SR-020
    relation: verifies
  - target: SR-027
    relation: verifies
  - target: SR-037
    relation: verifies
  - target: SR-038
    relation: verifies
  - target: SR-039
    relation: verifies
tags:
  - level:unit
  - class:B
---

# TS-012 — Usability, responsiveness and theming verification

## Scope

Software requirements covered: SR-019, SR-020, SR-027, SR-037, SR-038, SR-039.
Software items under test: SI-FE-SHELL, SI-FE-CORE.
Levels: unit.

## Preconditions and environment

Build: branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 20 with `frontend/package-lock.json`.
Unit and service tests run with no external services (jsdom; no browser matrix). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-012.1 | SR-020, SR-027 | `frontend/src/core/layout/AppLayout.test.tsx`, `frontend/src/core/nav/AppNavigation.test.tsx`, `frontend/src/core/nav/useNavItems.test.ts` | Layout and navigation adapt and stay consistent per role | Breakpoint and role variants asserted |
| TC-012.2 | SR-027 | `frontend/src/core/confirm/ConfirmDialog.test.tsx`, `frontend/src/core/error/AppErrorBoundary.test.tsx` | Destructive actions are confirmed and errors are surfaced clearly | Confirm and cancel paths asserted |
| TC-012.3 | SR-037, SR-038 | `frontend/src/core/theme/theme.test.ts`, `frontend/src/core/theme/StatusPill.test.tsx` | Tokens resolve in both modes and meet the contrast targets | Contrast computed per token pair |
| TC-012.4 | SR-039 | `frontend/src/core/theme/ModeToggle.test.tsx` | The mode toggle follows the system default and persists the choice | System, light and dark asserted |
| TC-012.5 | SR-027 | `frontend/src/core/profile/ProfilePage.test.tsx`, `frontend/src/core/layout/SignOutButton.test.tsx` | Profile and sign-out behave consistently | Rendering and action asserted |

## Acceptance criteria (class B unit level, §5.5.3)

- Boundary: the smallest supported viewport renders without horizontal scroll.
- Usability: the safe choice is the default in destructive dialogs (currently PRB-031).

## Notes

SR-019 cross-browser support cannot be verified in jsdom; it needs the browser matrix run of TASK-111 and is reported as unverified in TR-001.
