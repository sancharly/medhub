---
id: "PRB-090"
type: problem-report
title: "Idle warning dialog redirects to sign-in without clearing the cached clinical data"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-14"
updated: "2026-11-14"
criticality: major
links: []
tags: ["session", "frontend", "privacy", "found-in:TASK-222"]
---

# PRB-090 — Idle warning dialog redirects to sign-in without clearing the cached clinical data

## Observed

Found while implementing TASK-222. `IdleWarningDialog` (`frontend/src/auth/IdleWarningDialog.tsx`) has two redirects of its own to `/login?timeout=1` that do not clear the query cache:

- `handleExtend`: when `POST /auth/session/extend` answers 401 (`AuthError`), it only calls `navigate("/login?timeout=1")`.
- The countdown interval: when the remaining time reaches 0 it calls `navigate("/login?timeout=1")`. `handleExpired` (`SessionActivityProvider`) normally runs first at the same deadline and unmounts the dialog; the interval is a second, redundant owner of the same redirect.

## Impact

For the extend case: the server session has already ended (401) but the TanStack Query cache keeps every response the user loaded. Going Back after the redirect re-mounts the authenticated layout, and `RequireAuth` finds `me` in success state, so the cached clinical views render again with no re-authentication. This is the PRB-089 failure through a different path. The countdown case is the same if the interval ever fires before the deadline timer.

## Investigation

TASK-144 added the mutation-cache `AuthError` handler (clear + redirect) and TASK-222 made `handleExpired` end the session; the dialog, a separate component with its own `useNavigate`, was not changed by either. Its tests (`IdleWarningDialog.test.tsx`, "extend 401 redirects to login") assert only the navigation.

## Safety evaluation

Same as PRB-089 (RISK-001, severity 2: protected health information shown to a person with no right to it). Narrower trigger: it needs the server session to have ended while the warning is open (extend answered 401). Criticality `major` for the same control (SR-030 AC 1, AC 2). No released version is in clinical use (CR-004 D-21), so no notification is needed.

## Resolution

Fixed in CR-006 by TASK-222 (human decision, 2026-11-14: PRB-090 comes into CR-006 and TASK-222). QA's round-2 probe showed the countdown case is not hypothetical: after a wall-clock jump (laptop sleep, suspended tab) the dialog's overdue 500 ms tick is due before the expiry timeout, so the dialog's redirect won, unmounted the provider and cancelled `handleExpired` (no logout, no cache clear).

- `IdleWarningDialog.tsx` has a new `onExpired` prop and no `useNavigate`. Its countdown reaching zero and an extend answered 401 both call `onExpired()`.
- `SessionActivityProvider.tsx` passes `onExpired={handleExpired}`. `handleExpired` returns at once when `sessionEnded.current` is set, so the first caller (dialog tick or expiry timer) ends the session and a second call does not send a second logout.
- The mutation `AuthError` handler and "Log out now" set `sessionEnded` and leave the clear to the unmount cleanup, like the timeout.

Tests (TS-001 TC-001.13): `clock jump with the warning open: one logout, an empty cache and one redirect`, `the dialog's tick and the expiry timer firing in one pass log out once`, `extend 401 then Back shows no clinical data`; `IdleWarningDialog.test.tsx` `extend 401 reports the ended session through onExpired`, `the countdown reaching zero reports the ended session through onExpired once`. Negative controls: the dialog navigating directly fails 4 tests; no idempotence guard fails the one-pass test. Not yet confirmed through a shipped release, so `resolved`, not `closed`.
