---
id: "TASK-140"
type: task
title: "Auth config hygiene: remove dead session_signing_key, make lockout_svc required"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-030"
    relation: relates_to
  - target: "SR-029"
    relation: relates_to
  - target: "TASK-118"
    relation: relates_to
  - target: "TASK-003"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:low"]
---

- **Phase:** Review 2026-07 — backend security/robustness
- **Depends on:** —
- **Branch:** `chore/auth-config-hygiene`
- **Status:** Not started
- **Source:** `docs/reports/CODE-REVIEW-2026-07.md` — findings G + J (Low)

## Objective

Two hygiene items with security-adjacent weight:

1. `session_signing_key` is a **required** `SecretStr` setting (`app/core/config.py:31`, seeded in
   `infra/.env.example`) but referenced nowhere — sessions are opaque random tokens, not signed.
   Operators are forced to provision a secret that does nothing; its presence falsely implies
   sessions are signed.
2. `LoginService.login` accepts `lockout_svc` as an optional parameter defaulting to `None`
   (`app/auth/login.py`). The router wires it today (TASK-118), but the optional shape means any
   future caller that omits it silently disables brute-force protection.

## Implementation detail

- Delete `session_signing_key` from `Settings`, `infra/.env.example`, and deployment docs; note the
  removal in `infra/DEPLOY.md` changelog section.
- Make `lockout_svc` a required constructor/parameter dependency of `LoginService` (no `= None`);
  adjust tests that constructed it without lockout to pass a fake.

## Acceptance criteria

- [ ] App boots without `SESSION_SIGNING_KEY` in the environment; setting it is no longer required
  anywhere (compose, tests conftest, docs).
- [ ] Constructing/calling the login flow without a lockout service is a type/runtime error, not a
  silent bypass.
- [ ] Full auth test suite passes.

## Definition of Done

- [ ] Lint + type-check pass
- [ ] Conftest/env fixtures updated
- [ ] Traceability rows updated (SR-029/SR-030 references)
