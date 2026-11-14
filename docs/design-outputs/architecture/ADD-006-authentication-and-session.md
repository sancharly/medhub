---
id: ADD-006
type: architecture-doc
title: Authentication & Session (SI-AUTH)
status: in_review
version: "1.5"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-14"
links:
  - target: SR-002
    relation: implements
  - target: SR-025
    relation: implements
  - target: SR-029
    relation: implements
  - target: SR-030
    relation: implements
  - target: SR-034
    relation: implements
  - target: RISK-005
    relation: relates_to
  - target: SOUP-011
    relation: relates_to
  - target: SOUP-012
    relation: relates_to
  - target: SOUP-013
    relation: relates_to
  - target: SOUP-021
    relation: relates_to
tags:
  - software-item:SI-AUTH
  - class:B
  - layer:backend
---

# ADD-006 — Authentication & Session (SI-AUTH)

## Responsibility

Login, logout, password change, session lifecycle, lockout

## Software units (IEC 62304 §5.4.1)

- `U-AUTH-Login` — credential verification (Argon2id), generic failure (SR-002). The lockout
  service is a required, typed dependency; no call path can omit it (SR-029 AC 1, PRB-018). The
  unused `session_signing_key` setting is removed. A failed attempt is counted before it is
  audited, so a refused audit write cannot skip the count. A login that evicted a session reports it
  (`evicted_session`), which the login page shows as the notification of SR-030 AC 7 (PRB-066);
  cap contention that does not clear is answered 503 with `Retry-After: 1` and stores no session.
- `U-AUTH-Lockout` — failed-attempt counter, 5/30-min lock, admin unlock (SR-029).
- `U-AUTH-Session` — Redis session create/refresh/invalidate, role timeouts, absolute lifetime,
  concurrency cap (SR-030). The cap check, the eviction of the oldest live session and the
  insertion of the new one are one optimistic Redis transaction (`WATCH` on the account's sorted
  set, `MULTI`/`EXEC`, bounded retry), so concurrent logins cannot exceed the cap (SR-030 AC 7,
  PRB-023). The cap transaction counts only live members (a `session:{id}` key exists), evicts the
  oldest live one and removes expired members from the sorted set in the same `MULTI`/`EXEC`
  (PRB-065). The refresh is a conditional write (`SET … EX … XX`): a session key deleted by
  logout, eviction or the password-change session kill is never written again, and `resolve()`
  then answers "ended" (SR-030 AC 5, PRB-064).
  **CR-006 (TASK-144):** the remaining lifetime (`SessionService.remaining_seconds`: the smaller of the
  role's idle timeout and the absolute remainder, never negative) is read by the route; `GET /me` reports it as
  `sessionExpiresInSeconds` and the extend response as `expiresInSeconds` next to `expiresAt`, so the
  client's deadline follows the server (SR-030 AC 8). Additive response fields; the session decision
  is unchanged. The session dependencies run in the thread pool (ADR-0022, ADD-005).
  **CR-006 (TASK-221):** `resolve(session_id, slide=False)` validates the session (it exists and is inside
  its absolute lifetime) and writes nothing; the dependencies `get_session_no_slide` and
  `get_current_user_no_slide` use it and serve only `GET /me/modules`, which the client polls on a timer
  (SR-015 AC 5). A background poll therefore cannot keep an idle session alive; every other route still
  slides the session on resolve (SR-030 AC 1, AC 2; RISK-005).
- `U-AUTH-PasswordPolicy` — server-side complexity, history(12), max-age(180d), reuse/username checks (SR-025).
- `U-AUTH-Cookie` — Secure/HttpOnly/SameSite=Strict cookie issuing (SR-030.6).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-002, SR-025, SR-029, SR-030, SR-034.
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
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0011](../../design/adr/), [ADR-0012](../../design/adr/), [ADR-0013](../../design/adr/), [ADR-0012](../../design/adr/0012-authentication-session-mechanism.md).

## Risk relevance

Participates in RISK-005 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): unit changes for the planned design added (marked "CR-004"), links added. Content change, so the approval record is cleared and the record returns to review. The implementing tasks confirm the unit text when they land.
- 1.2 (2026-11-06) — TASK-205 (CR-004 D-11): `U-AUTH-Session` refresh is a conditional write; the cap counts live members and prunes dead ones in the same transaction; `U-AUTH-Login` reports the eviction and answers cap contention 503. Content change, so the 1.1 approval record is cleared and the record returns to review.
- 1.3 (2026-11-08) — TASK-201 (CR-004): the "CR-004 change" unit notes merged into the unit text as built; `U-AUTH-Login` notes that a failed attempt is counted before it is audited. No change of meaning. Arc42 sections 05, 06 and 12 updated.
- 1.4 (2026-11-13) — CR-006 Plan stage (Software Architect role): `U-AUTH-Session` reports the remaining session seconds through `GET /me` and extend (SR-030 AC 8), marked "CR-006 (planned)". Content change, so the 1.3 approval record is cleared and the record returns to review.
- 1.5 (2026-11-14) — TASK-144 (CR-006): "CR-006 (planned)" removed from `U-AUTH-Session`; `SessionService.remaining_seconds` feeds `sessionExpiresInSeconds` (`GET /me`) and `expiresInSeconds` (extend). Content change, so the 1.4 approval record is cleared and the record returns to review.
- 1.5 (2026-11-14) — TASK-144 QA round 1: `sessionExpiresInSeconds` is required on `GET /me`; `POST /auth/password` answers a wrong current password with 400 `validation-error` (`currentPassword`), not 401, because a 401 means "no valid session" to the client. Still `in_review`.
- 1.5 (2026-11-14) — TASK-221 (CR-006, SR-030 AC 1, AC 2): `U-AUTH-Session` gains `resolve(..., slide=False)` and the non-sliding dependencies for `GET /me/modules`. Still `in_review`.
