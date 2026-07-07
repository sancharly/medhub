---
id: "TASK-084"
type: task
title: "Error boundary + toast rendering RFC 7807 problem+json"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-027"
    relation: implements
  - target: "TASK-081"
    relation: relates_to
tags: ["audit-verified", "phase:6-frontend-foundation"]
---

- **Phase:** 6 — Frontend foundation
- **Software item / unit:** SI-FE-SHELL / U-FE-Error
- **Implements:** SR-027 (AC-3 clear, actionable message identifying the problem when an operation fails or input is invalid)
- **Depends on:** TASK-081 (AppLayout + MUI theme) — must be merged first
- **Branch:** `feature/fe-error-boundary`
- **Status:** Completed (audit-verified 2026-06-29)

## Objective

Provide the SPA's **single error surface**: a React error boundary that catches render-time failures without crashing the shell, plus a toast/inline mechanism that renders backend **RFC 7807 `application/problem+json`** errors as clear, actionable messages identifying the problem (SR-027 AC-3). Centralizing it means every failed operation and every invalid-input response is presented consistently — using the problem document's `detail` and field-level `errors[]` — rather than each view inventing its own. It consumes the typed `ProblemError` produced by the API client (TASK-080). Traces to SR-027.3.

## Interfaces to honor

Provides the error half of `ShellServices` from [12-interfaces.md](../../design/12-interfaces.md) §12.2 (provider SI-FE-SHELL; consumers SI-FE-CORE, modules) and consumes the typed problem error from the API client:

```ts
// ProblemError is produced by the ApiClient (TASK-080) from application/problem+json
type ProblemError = { type: string; title: string; status: number; detail?: string; errors?: { field: string; message: string }[] };

interface ShellErrorServices {
  errorToast(error: ProblemError | Error): void;   // global toast surface
}
// plus a render-error boundary wrapping the routed content
function AppErrorBoundary(props: { children: React.ReactNode }): React.ReactNode;
```

- Renders into the shell (TASK-081); the toast surface is a single mounted instance exposed via `ShellServices.errorToast(...)`.
- Maps the RFC 7807 document to user-facing text: prefer `detail`, fall back to `title`; when `errors[]` is present (e.g. `400 /errors/validation-error`), surface the field-level messages so the user can fix the input (SR-027 AC-3). The error `type` URIs are those in [api-design.md](../../specifications/api-design.md)'s error catalog.
- Must **not**: display raw stack traces, internal exception text, or any PHI in error UI; treat `401 /errors/unauthenticated` as a toast — that is the auth boundary's concern (redirect to login, TASK-085); re-implement HTTP/CSRF handling (that is TASK-080). The boundary catches **render** errors; network/API errors arrive as `ProblemError` via TanStack Query.

## Implementation detail

- Files to create:
  - `frontend/src/core/error/AppErrorBoundary.tsx` — a React error boundary (class component) wrapping routed content; on a render error it shows a recoverable fallback panel (with a retry/reset) and keeps the shell chrome intact (SR-027 AC-3).
  - `frontend/src/core/error/ErrorToastProvider.tsx` — context provider holding the toast queue; exposes `errorToast(error)`; renders MUI `Snackbar`/`Alert`.
  - `frontend/src/core/error/problemToMessage.ts` — pure mapper `ProblemError -> { summary: string; fieldErrors?: {field,message}[] }`: prefers `detail`, falls back to `title`, expands `errors[]`; never emits stack/internal text.
  - `frontend/src/core/error/useErrorToast.ts` — hook returning `errorToast(...)`.
  - `frontend/src/core/error/index.ts` — exports boundary, provider, hook, mapper.
  - Mount `AppErrorBoundary` + `ErrorToastProvider` at the shell root (TASK-081).
- Libraries (exact stack): React 18 (error boundary), MUI `Snackbar`/`Alert`, TypeScript; consumes `ProblemError` from TASK-080.
- Field-level validation errors (`400 /errors/validation-error` with `errors[]`, SR-010/SR-012/SR-025/SR-032) are made available to forms so they can show messages next to the offending field (the auth/password/activation forms in TASK-085/086/087 consume `fieldErrors`); generic non-field failures show a toast (SR-027 AC-3).
- The mapper is the single place message text is derived, keeping wording consistent (SR-027 AC-1).
- This unit owns no routes, no API calls, no PHI.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit tests (Vitest), `frontend/src/core/error/problemToMessage.test.ts`:
  - a `ProblemError` with `detail` → summary uses `detail`; with only `title` → falls back to `title` (SR-027 AC-3).
  - a `400 /errors/validation-error` with `errors[]` → produces per-field messages for forms (SR-027 AC-3).
  - never emits stack traces or internal exception text.
- Component tests (Vitest + React Testing Library), `frontend/src/core/error/AppErrorBoundary.test.tsx`:
  - a child that throws during render is caught; the fallback renders with the shell intact and a retry/reset (SR-027 AC-3) — no white-screen crash.
  - `errorToast(problem)` renders an MUI alert with the mapped, actionable message (SR-027 AC-3).
  - a `401 /errors/unauthenticated` is **not** toasted here (delegated to the auth boundary, TASK-085).
- Each test names the SR AC it verifies.

## Acceptance criteria

- [x] Backend RFC 7807 `application/problem+json` errors are rendered as clear, actionable messages using `detail`/`title` and field-level `errors[]` (SR-027 AC-3).
- [x] A render-time error is caught by the boundary; the shell stays usable with a recoverable fallback (SR-027 AC-3).
- [x] No stack traces, internal text, or PHI appear in any error UI.
- [x] `401 /errors/unauthenticated` is delegated to the auth boundary (TASK-085), not toasted.
- [x] Message derivation is centralized so wording is consistent (SR-027 AC-1).

## Definition of Done

- [x] Lint + type-check pass (`eslint`/`tsc`)
- [x] Unit/component tests pass; coverage target met
- [x] Traceability matrix row updated (SR-027 → TASK-084 → tests)

## Audit verdict (2026-06-29)

- **Verdict:** PASS
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- Acceptance criteria verified met; boxes checked.
