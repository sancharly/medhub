---
id: "PRB-003"
type: problem-report
title: "CSRF exemption list matches by prefix, so future sibling routes are silently exempt"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-31"
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

Planned in [CR-004](../change-requests/CR-004-close-open-security-defects-from-2026-07-review.md):
TASK-139 (exact-path exemptions, the activation path matched as one path segment, the dead
password-reset entry removed, and a route-inventory test). Not yet fixed.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding F.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
