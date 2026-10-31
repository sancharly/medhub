---
id: "PRB-018"
type: problem-report
title: "A required secret is unused and the lockout service is an optional parameter"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-31"
criticality: minor
links: []
tags: ["security", "configuration-management"]
---

# PRB-018 — A required secret is unused and the lockout service is an optional parameter

## Observed

`session_signing_key` is a required `SecretStr` (`app/core/config.py:31`, seeded in `infra/.env.example`) that nothing reads — sessions are opaque random tokens, not signed — and `LoginService.login` takes `lockout_svc` defaulting to `None`, so a future caller can omit brute-force protection silently.

## Impact

Operators provision a secret that does nothing, which falsely implies signed sessions; the optional parameter shape invites a regression against SR-029.

## Investigation

Read on 2026-10-31 (CR-004 Plan stage, Software Architect role). **Present as reported.**

- `backend/app/core/config.py:31` declares `session_signing_key: SecretStr` as required. Nothing
  under `backend/app` or `backend/modules` reads it. Sessions are `secrets.token_urlsafe(32)`
  values stored in Redis (`backend/app/auth/session.py:78,108`). It is still required in
  `infra/.env.example:38`, `infra/DEPLOY.md:18`, `backend/tests/conftest.py:21`,
  `backend/tests/test_config.py:15`, `backend/tests/test_lifespan.py:17`,
  `backend/modules/dicom_viewer/tests/conftest.py:25` and `.github/workflows/ci.yml:79,167`.
- `LoginService.login` takes `lockout_svc: object | None = None` (`backend/app/auth/login.py:66`)
  and skips every lockout step when it is `None` (`login.py:88-90,97,118-119,123-124`). The only
  production caller passes it (`backend/app/api/routers/auth.py:59-60`).

## Safety evaluation

Contributes to RISK-005 (account takeover) only through the optional-parameter shape; no live bypass, since the router wires the service today (TASK-118).

## Resolution

Planned in CR-004: TASK-140 (setting removed everywhere; `lockout_svc` a required, typed
dependency). Not yet fixed.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` findings G and J.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
