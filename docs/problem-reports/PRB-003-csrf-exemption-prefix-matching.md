---
id: "PRB-003"
type: problem-report
title: "CSRF exemption list matches by prefix, so future sibling routes are silently exempt"
status: open
criticality: major
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["security", "hazard:security"]
---

# PRB-003 — CSRF exemption list matches by prefix, so future sibling routes are silently exempt

## Observed

The CSRF middleware matches exemptions with `startswith`, and two entries (`/api/v1/auth/password-reset`, `/api/v1/activation`) have no trailing slash (`app/core/security_middleware.py`). Any future route whose path starts with those strings is exempted without anyone deciding so. No live bypass exists today.

## Impact

Weakens the CSRF control behind SR-031 by making its scope depend on future route names rather than an explicit decision.

## Safety evaluation

Contributes to RISK-005 (account takeover leading to disclosure or falsified clinical records). Not realized today, so no harm has occurred.

## Resolution

TASK-139 (draft) — exact-match exemptions with a trailing-slash-normalized comparison and a test that a sibling route is not exempt. The CR that closes this PRB is that task's merge.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding F.
