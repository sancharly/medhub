---
id: "TASK-139"
type: task
title: "CSRF exemption exact-match hardening"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-031"
    relation: implements
  - target: "TASK-128"
    relation: relates_to
  - target: "TASK-069"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:medium"]
---

- **Phase:** Review 2026-07 — backend security/robustness
- **Implements:** SR-031 (web vulnerability mitigations)
- **Depends on:** —
- **Branch:** `fix/csrf-exempt-exact-match`
- **Status:** Not started
- **Source:** `docs/reports/CODE-REVIEW-2026-07.md` — finding F (Medium)

## Objective

`CsrfEnforcementMiddleware` exempts paths via `startswith` over `_CSRF_EXEMPT_PREFIXES`
(`app/core/security_middleware.py:53-61,86-88`). Two prefixes lack a trailing slash
(`/api/v1/auth/password-reset`, `/api/v1/activation`), so **any future sibling route** sharing the
prefix (e.g. `/api/v1/activation-admin`, `/api/v1/auth/password-reset-force`) is silently
CSRF-exempt. No live bypass exists today; the pattern is a latent footgun.

## Implementation detail

- Replace prefix matching with an explicit exact-path set (plus a documented, deliberate prefix
  entry only where a path parameter follows, e.g. `/api/v1/activation/{token}` — match via
  `re.fullmatch` or route-level marker).
- Preferred: move exemption to route level (dependency marker / router-registered exempt set) so
  exemptions live next to the route definitions they cover.
- Add a test enumerating all mounted unsafe-method routes and asserting each is either
  CSRF-enforced or on the reviewed exemption list (fails when a new route silently matches).

## Acceptance criteria

- [ ] A hypothetical sibling route (`/api/v1/activation-x`) is CSRF-enforced (regression test).
- [ ] All current exempt paths (login, password-reset, activation, anonymized-data retrieval,
  health, openapi) still work sessionless.
- [ ] Route-inventory test fails on unreviewed exemptions.

## Definition of Done

- [ ] Lint + type-check pass
- [ ] `tests/api/test_csrf_enforcement.py` extended with the inventory + sibling-route cases
- [ ] Traceability row updated (SR-031 → TASK-139 → tests)
