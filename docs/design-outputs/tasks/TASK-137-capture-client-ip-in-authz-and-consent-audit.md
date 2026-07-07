---
id: "TASK-137"
type: task
title: "Capture client IP in authorization and consent audit records"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-023"
    relation: implements
  - target: "TASK-027"
    relation: relates_to
  - target: "TASK-014"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:medium"]
---

- **Phase:** Review 2026-07 — backend security/robustness
- **Implements:** SR-023 (audit logging of security-relevant events)
- **Depends on:** —
- **Branch:** `fix/audit-client-ip`
- **Status:** Not started
- **Source:** `docs/reports/CODE-REVIEW-2026-07.md` — finding D (Medium)

## Objective

Every `AUTHZ_ALLOWED` / `AUTHZ_DENIED` audit record is written with `ip=None`
(`app/authz/service.py:71,80`); ConsentService records likewise. Only login/logout/password flows
propagate `request.client.host`. Forensic reconstruction of an access-control incident (who tried
what, from where) is impossible for the majority of security-relevant events — an SR-023 gap.

## Implementation detail

- Introduce request-scoped actor context: a `contextvars.ContextVar` set by a small middleware (or
  the `get_session` dependency) holding client IP (honoring `X-Forwarded-For` from the trusted
  reverse proxy only).
- `AuditService.record` reads the contextvar as default when `ip` is not supplied; explicit `ip`
  arguments keep precedence. Worker-context records legitimately stay `ip=None`.
- No signature churn across services — the contextvar avoids threading `Request` through
  `AuthorizationService`/`ConsentService`.

## Acceptance criteria

- [ ] Authz allow/deny and consent grant/revoke audit rows carry the originating client IP for
  request-scoped operations.
- [ ] Worker/beat-originated audit rows still record `ip=None` without error.
- [ ] `X-Forwarded-For` is honored only from the reverse proxy, not spoofable by clients directly.

## Definition of Done

- [ ] Lint + type-check pass
- [ ] Integration test asserts IP present on a 403 authz-denied audit row
- [ ] Traceability row updated (SR-023 → TASK-137 → tests)
