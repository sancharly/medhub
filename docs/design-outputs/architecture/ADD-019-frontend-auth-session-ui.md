---
id: ADD-019
type: architecture-doc
title: Frontend Auth/Session UI (SI-FE-AUTH)
status: approved
version: "1.4"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-16"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-16"
approved_digest: a8d130485a0f73faf83ab37070d58276f2e518d842e94e511000412efc97fd52
approval_note: self-approved
links:
  - target: SR-026
    relation: implements
  - target: SR-002
    relation: implements
  - target: SR-025
    relation: implements
  - target: SR-030
    relation: implements
  - target: SR-033
    relation: implements
  - target: RISK-005
    relation: relates_to
  - target: SOUP-025
    relation: relates_to
  - target: SOUP-027
    relation: relates_to
  - target: SOUP-028
    relation: relates_to
tags:
  - software-item:SI-FE-AUTH
  - class:B
  - layer:frontend
---

# ADD-019 — Frontend Auth/Session UI (SI-FE-AUTH)

## Responsibility

Login, activation, password, inactivity warning/extend

## Software units (IEC 62304 §5.4.1)

- `U-FEA-LoginForm`, `U-FEA-Activation`, `U-FEA-PasswordForm`, `U-FEA-IdleWarning` (SR-002, SR-025, SR-030.4, SR-033).
- **CR-006.** `U-FEA-Me` (TASK-144, built): `useMe()` is the only reader of the `me` query
  (`retry: false`, a 30-second stale time); a 401 on a mutation (the attachment upload included) clears
  the cache and redirects once to `/login?timeout=1` (`SessionActivityProvider` registers the handler
  that the query client's mutation cache calls; a 401 on `me` itself is redirected by `RequireAuth`).
  `U-FEA-IdleWarning` (TASK-144, built): the
  deadline is the receipt time of the `me` or extend response plus the session seconds the server
  reports (`sessionExpiresInSeconds`, `expiresInSeconds`; relative, so the client clock does not move
  it); no client timeout constant (SR-030 AC 8, AC 4). `U-FEA-IdleTimer` (TASK-222, built): the
  timers are armed only from that server-derived deadline (the newer of the `me` and the extend
  response); there are no activity listeners, so mouse, key, click, touch and scroll events do no
  session-timer work (SR-026 AC 8, SR-030 AC 8). The user keeps the session by making a request that
  refreshes `me` or by pressing Extend. When the deadline passes the client ends the session
  (PRB-089, SR-030 AC 1, AC 2, AC 5): `apiClient.logout()` is started and not awaited (its error is
  ignored and never reaches the `AuthError` handler), the redirect to `/login?timeout=1` is made once,
  and the query cache is cleared as that redirect unmounts the signed-in tree, so Back renders no
  cached clinical data (RISK-001). Clearing while `me` observers are mounted would make them refetch
  `me` (SOUP-028). `U-FEA-IdleWarning` does not navigate: its countdown reaching zero and an extend
  answered 401 call `onExpired`, which is the provider's `handleExpired` (idempotent: the first call
  wins), so the session end has one owner (PRB-090). A 401 on a mutation and "Log out now" use the same
  clear-on-unmount. Server enforcement of SR-030 AC 1 to AC 3 is unchanged (RISK-005).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-002, SR-025, SR-030, SR-033; SR-026 (AC 8, added by CR-006).
Non-functional requirements constraining this item: —.

## Interfaces

Provided and consumed interfaces are specified in
[12-interfaces.md](../../design/12-interfaces.md); the runtime interactions this item takes part in
are in [06-runtime-views.md](../../design/06-runtime-views.md) and the sequence diagrams under
[`../../specifications/`](../../specifications/).

## Architecture narrative

This record is a summary and traceability anchor, not the narrative. The design itself is in the
arc42 sections — [05 building blocks](../../design/05-building-blocks.md) for the decomposition,
[04 solution strategy](../../design/04-solution-strategy.md),
[08 cross-cutting concepts](../../design/08-cross-cutting-concepts.md) and, for deployment,
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0011](../../design/adr/), [ADR-0012](../../design/adr/).

## Risk relevance

Participates in RISK-005 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.

## Version history

- 1.1 (2026-11-13) — CR-006 Plan stage (Software Architect role): one `me` query, client deadline from the server-reported session seconds, and throttled activity tracking marked "CR-006 (planned)"; `implements` SR-026 added. Content change, so the 1.0 approval record is cleared and the record returns to review.
- 1.2 (2026-11-14) — TASK-144 (CR-006): `U-FEA-Me` and the server-derived deadline of `U-FEA-IdleWarning` marked as built; the throttled activity tracking (TASK-222) stays planned. Content change, so the 1.1 approval record is cleared and the record returns to review.
- 1.2 (2026-11-14) — TASK-144 QA round 1: the PRB-087 limitation named. Still `in_review`.
- 1.3 (2026-11-14) — TASK-222 (CR-006 D-33): `U-FEA-IdleTimer` changed from planned (re-arm at most once per second) to built (deadline only from server responses, no activity listeners); the PRB-087 limitation removed; the timeout's session end (logout, cache clear, one redirect) added. Content change. (The MedTrace approval of 1.3 was given by the human on 2026-11-14, before QA; the earlier wording "still `in_review`" was wrong.)
- 1.4 (2026-11-14) — TASK-222 round 2 (QA, PRB-090): `U-FEA-IdleWarning` reports expiry through `onExpired` instead of navigating; `handleExpired` idempotent; the `AuthError` and logout paths clear on unmount. Content change, so the approval of 1.3 is cleared: `in_review`.
