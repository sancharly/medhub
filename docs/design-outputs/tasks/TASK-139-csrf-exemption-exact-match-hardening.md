---
id: "TASK-139"
type: task
title: "CSRF exemption exact-match hardening"
status: draft
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-10-31"
links:
  - target: "SR-031"
    relation: implements
  - target: "RISK-005"
    relation: mitigates
  - target: "RISK-001"
    relation: mitigates
  - target: "PRB-003"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "ADD-005"
    relation: relates_to
  - target: "TASK-128"
    relation: relates_to
  - target: "TASK-069"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:medium", "control:design", "cr:CR-004"]
---

# TASK-139 — CSRF exemption exact-match hardening

- **Software item / unit:** SI-API `U-API-Security` (ADD-005), `backend/app/core/security_middleware.py`.
- **Resolves (through CR-004):** PRB-003. Source: `docs/reports/CODE-REVIEW-2026-07.md` finding F.
- **Depends on:** none. Independent; can run in parallel with any CR-004 task.
- **Branch:** `fix/review-2026-07-security` (CR-004).
- **Size:** S (1 source file, 1 test file, TS-011)

## Objective

SR-031 AC 3: CSRF protection on every state-changing route that is not deliberately exempt.
`CsrfEnforcementMiddleware` exempts by `startswith` (`security_middleware.py:53-61,86-88`), so a
future sibling of `/api/v1/activation` or `/api/v1/auth/password-reset` would be exempt silently.
The PRB-003 Investigation also found that no password-reset route exists.

## Implementation detail

- Replace `_CSRF_EXEMPT_PREFIXES` with two explicit structures: a `frozenset` of exact paths
  (`/api/v1/auth/login`, `/api/v1/healthz`, `/api/v1/openapi.json`, `/healthz`,
  `/api/v1/anonymized-data/retrieve`) and a tuple of compiled `re.fullmatch` patterns for
  routes with a path parameter (`^/api/v1/activation/[^/]+$`). Compare the path with a trailing
  slash removed.
- Remove the `/api/v1/auth/password-reset` entry (no such route).
- Each entry carries a comment naming the route and why it has no session (ADR-0013 for the
  retrieval).

## Tests (write first)

`backend/tests/api/test_csrf_enforcement.py` (extend):

- `POST /api/v1/activation-x`, `POST /api/v1/auth/password-reset-force`,
  `POST /api/v1/anonymized-data/retrieve-all` and `POST /api/v1/activation/abc/extra` without a
  CSRF token → 403 problem+json (sibling routes are enforced);
- the current exempt routes still work without a session or token (login, activation with a
  token, retrieval, health);
- route inventory: enumerate `create_app().routes` for unsafe methods; each is either enforced
  or matched by an exemption that is in a reviewed list in the test; a new route that matches
  no reviewed entry but is exempt fails the test.

## Acceptance criteria

- [ ] SR-031 AC 3: sibling routes are CSRF-enforced (`backend/tests/api/test_csrf_enforcement.py`).
- [ ] The current exempt routes work sessionless (same file).
- [ ] The inventory test fails on an unreviewed exemption (negative control: add a prefix entry back).

## Verification

```sh
cd backend && uv run pytest tests/api/test_csrf_enforcement.py tests/api/test_activation_router.py tests/api/test_anonymized_retrieve.py -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
```

## Records

- **TS-011** → 1.2 (`in_review`): TC-011.6 (exact exemptions, siblings enforced, inventory),
  `verifies` SR-031.
- **PRB-003**: `## Resolution`, `resolved`.

## Definition of Done

- [ ] Lint, type-check, backend suite pass; coverage ≥ 85 %.
- [ ] TS-011 1.2 `in_review`; PRB-003 `resolved`; TASK-113's security-review checklist item for
      CSRF re-run (auth/session code review gate, SR-031 AC 6).
- [ ] `traceability-check` shows no error for TASK-139, TS-011, SR-031, PRB-003.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): rescoped against the current
  tree (no password-reset route; the activation route has a path parameter). Links `mitigates`
  RISK-005, RISK-001 and `relates_to` PRB-003, CR-004, ADD-005 added; tagged `control:design`.
  Tests named by path, TS-011 TC-011.6 planned. Still `draft`.
