---
id: "PRB-003"
type: problem-report
title: "CSRF exemption list matches by prefix, so future sibling routes are silently exempt"
status: resolved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-02"
criticality: major
links: []
tags: ["security", "hazard:security"]
---

# PRB-003 — CSRF exemption list matches by prefix, so future sibling routes are silently exempt

## Observed

The CSRF middleware matches exemptions with `startswith`, and two entries (`/api/v1/auth/password-reset`, `/api/v1/activation`) have no trailing slash (`app/core/security_middleware.py`). Any future route whose path starts with those strings is exempted without anyone deciding so. No live bypass exists today.

## Impact

Weakens the CSRF control behind SR-031 by making its scope depend on future route names rather than an explicit decision.

## Investigation

Read on 2026-10-31 (CR-004 Plan stage, Software Architect role) against branch
`fix/review-2026-07-security`. **The defect is still present as reported.**

- `backend/app/core/security_middleware.py:53-61` declares `_CSRF_EXEMPT_PREFIXES`, and
  `security_middleware.py:86-88` exempts any unsafe request whose path `startswith` one of them.
- Two entries have no trailing separator: `/api/v1/auth/password-reset` and `/api/v1/activation`.
  Any future path that begins with either string (`/api/v1/activation-admin`) is exempt.
- New fact: **no password-reset route exists** (`grep password-reset backend/app` matches only
  the middleware). The entry exempts a path nobody serves. The only activation route is
  `POST /api/v1/activation/{token}` (`backend/app/api/routers/activation.py:21,51`).
- The assumption that broke: "an exemption names a route". A prefix names every route that will
  ever share the prefix.

No live bypass: every route mounted today that matches a prefix is one that is meant to be
exempt.

## Safety evaluation

Contributes to RISK-005 (account takeover leading to disclosure or falsified clinical records). Not realized today, so no harm has occurred.

## Resolution

Fixed by [TASK-139](../design-outputs/tasks/TASK-139-csrf-exemption-exact-match-hardening.md), QA approved
2026-11-02 (CR-004 D-8: QA approval sets this report `resolved`; `closed` is a human step at release).

`backend/app/core/security_middleware.py` no longer matches by prefix. `_CSRF_EXEMPT_PREFIXES` is replaced by
`_CSRF_EXEMPT_PATHS` (a `frozenset` of five exact paths: `/api/v1/auth/login`,
`/api/v1/anonymized-data/retrieve`, `/api/v1/healthz`, `/api/v1/openapi.json`, `/healthz`) and
`_CSRF_EXEMPT_PATTERNS` (one `re.fullmatch` pattern, `/api/v1/activation/[^/]+`, for the route with a path
parameter), evaluated by `is_csrf_exempt(path)` with one trailing slash ignored. The dead
`/api/v1/auth/password-reset` entry is removed. Each entry carries a comment naming its route and why it has no
session (ADR-0013 for the retrieval).

Before the fix, 20 of the 25 characterised POST paths were exempt, including siblings such as
`/api/v1/activation-x`, `/api/v1/auth/password-reset-force`, `/api/v1/anonymized-data/retrieve-all`,
`/api/v1/activation/abc/extra` and `/healthz/deep`. After it, only the exact routes are exempt. Verification:
TS-011 TC-011.6 (`backend/tests/api/test_csrf_enforcement.py`), including a route inventory that fails when an
exempt entry or route is not in a reviewed list. Negative control: restoring prefix matching fails 16 tests (QA re-run, without the password-reset prefix: 14).
QA also probed path normalisation on the running app (double slashes, dot segments, `%2F`, case, `;params`,
query strings): no probe reached a non-exempt route without a token.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding F.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
- 1.2 (2026-11-02) — TASK-139 implemented: `## Resolution` written (fix ready). Status stays `open` until QA approval (CR-004 D-8).
- 1.3 (2026-11-02) — QA approved TASK-139: status `open` → `resolved` (CR-004 D-8). Criticality unchanged.
