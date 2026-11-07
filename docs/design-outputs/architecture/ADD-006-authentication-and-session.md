---
id: ADD-006
type: architecture-doc
title: Authentication & Session (SI-AUTH)
status: in_review
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-06"
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

- `U-AUTH-Login` — credential verification (Argon2id), generic failure (SR-002).
- `U-AUTH-Lockout` — failed-attempt counter, 5/30-min lock, admin unlock (SR-029).
- `U-AUTH-Session` — Redis session create/refresh/invalidate, role timeouts, absolute lifetime, concurrency cap (SR-030).
- `U-AUTH-PasswordPolicy` — server-side complexity, history(12), max-age(180d), reuse/username checks (SR-025).
- `U-AUTH-Cookie` — Secure/HttpOnly/SameSite=Strict cookie issuing (SR-030.6).
- `U-AUTH-Session` (CR-004 change) — the concurrency-cap check, the eviction of the oldest
  session and the insertion of the new one are one optimistic Redis transaction (`WATCH` on the
  account's sorted set, `MULTI`/`EXEC`, bounded retry), so concurrent logins cannot exceed the cap
  (SR-030 AC 7, PRB-023).
- `U-AUTH-Session` (CR-004 change, TASK-205) — the refresh is a conditional write (`SET … EX … XX`):
  a session key deleted by logout, eviction or the password-change session kill is never written
  again, and `resolve()` then answers "ended" (SR-030 AC 5, PRB-064). The cap transaction counts only
  live members (a `session:{id}` key exists), evicts the oldest live one and removes expired members
  from the account's sorted set in the same `MULTI`/`EXEC` (SR-030 AC 7, PRB-065).
- `U-AUTH-Login` (CR-004 change, TASK-205) — a login that evicted a session reports it
  (`evicted_session`), which the login page shows as the notification of SR-030 AC 7 (PRB-066); cap
  contention that does not clear is answered 503 with `Retry-After: 1` and stores no session.
- `U-AUTH-Login` (CR-004 change) — the lockout service is a required, typed dependency; no call
  path can omit it (SR-029 AC 1, PRB-018). The unused `session_signing_key` setting is removed.

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
