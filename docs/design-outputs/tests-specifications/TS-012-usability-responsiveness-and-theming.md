---
id: TS-012
type: test-specification
title: Usability, responsiveness and theming verification
status: approved
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-14"
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
dependencies locked in `backend/uv.lock`; frontend Node 24 LTS (build stage node:24.22.2-trixie-slim; CI node-version 24) with `frontend/package-lock.json`.
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
| TC-012.6 | SR-027 AC 3 (TASK-145) | `frontend/src/core/error/RouteChunkBoundary.test.tsx`: `lazy route renders after its chunk loads`, `failed chunk shows the retry message, retry recovers`, `a retry that fails again offers a page reload` (the "application may have been updated" message and a Reload button calling `window.location.reload()`, mocked), `navigating to a failing route imports its chunk once`, `moving to another route clears the failure`, `an error thrown by the page itself is left to the app boundary`; `frontend/src/core/layout/AppLayout.test.tsx`: `shows an accessible progress indicator while a lazy page loads, shell intact`, `shows the retry message when a lazy page fails to load, shell intact`. Negative control: the retry without `reloadFailedChunks()` | A lazy route waits behind an accessible progress indicator and renders when its chunk arrives; a chunk that fails to import shows "This page could not be loaded." with a Retry that imports it again (the import runs a second time and the page renders); a failed retry offers a page reload (a deployment can remove the old chunks); a failing route met by navigation is imported once; leaving the route clears it; a page's own render error is not reported as a loading failure; the navigation and header stay on screen throughout | All listed tests pass; without the rebuild on retry the recovery test fails (page never loads) and the second test sees one import instead of two |

## Acceptance criteria (class B unit level, §5.5.3)

- Boundary: the smallest supported viewport renders without horizontal scroll.
- Usability: the safe choice is the default in destructive dialogs (currently PRB-031).

## Notes

SR-019 cross-browser support cannot be verified in jsdom; it needs the browser matrix run of TASK-111 and is reported as unverified in TR-001.

## Version history

- 1.1 (2026-10-30): approved.
- 1.2 (2026-11-14): TASK-145. Added TC-012.6 (route chunk failure with a working retry, SR-027 AC 3). Content change, so the approval record is removed. `in_review`.
- 1.2 (2026-11-14): QA review of TASK-145 (round 1): `approved` (status only; content unchanged).
- 1.3 (2026-11-14): TASK-145 QA round 1 fixes. TC-012.6: a failed retry offers a reload; a failing route met by navigation is imported once. Content change, so the approval record is removed. `in_review`.
- 1.3 (2026-11-14): QA review of TASK-145 (round 2): `approved` (status only; content unchanged).
