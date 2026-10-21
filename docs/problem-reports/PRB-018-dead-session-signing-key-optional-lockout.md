---
id: "PRB-018"
type: problem-report
title: "A required secret is unused and the lockout service is an optional parameter"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
criticality: minor
links: []
tags: ["security", "configuration-management"]
---

# PRB-018 — A required secret is unused and the lockout service is an optional parameter

## Observed

`session_signing_key` is a required `SecretStr` (`app/core/config.py:31`, seeded in `infra/.env.example`) that nothing reads — sessions are opaque random tokens, not signed — and `LoginService.login` takes `lockout_svc` defaulting to `None`, so a future caller can omit brute-force protection silently.

## Impact

Operators provision a secret that does nothing, which falsely implies signed sessions; the optional parameter shape invites a regression against SR-029.

## Safety evaluation

Contributes to RISK-005 (account takeover) only through the optional-parameter shape; no live bypass, since the router wires the service today (TASK-118).

## Resolution

TASK-140 (draft) — remove the dead setting and make `lockout_svc` required.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` findings G and J.
