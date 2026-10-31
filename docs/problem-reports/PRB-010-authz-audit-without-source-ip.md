---
id: "PRB-010"
type: problem-report
title: "Authorization and consent audit records carry no source IP"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-31"
criticality: major
links: []
tags: ["security", "hazard:detectability"]
---

# PRB-010 — Authorization and consent audit records carry no source IP

## Observed

`authz/service.py:71,80` writes audit rows with `ip=None`; only the login, logout and password flows capture the source address.

## Impact

SR-023 requires security-relevant events to be reconstructable; without the origin, a wrong access cannot be attributed.

## Investigation

Read on 2026-10-31 (CR-004 Plan stage, Software Architect role). **Present as reported, and
wider.**

- `backend/app/authz/service.py:65-72,74-81` records `AUTHZ_ALLOWED` and `AUTHZ_DENIED` with
  `ip=None`. `backend/app/authz/consent.py:58-64,87-93,105-111` does the same for consent grant,
  revoke and the appointment-derived grants. So do the appointment, clinical, group, identity and
  lockout services (`ip=None` in each `record` call).
- The flows that do pass an address take `request.client.host` (`backend/app/api/routers/auth.py:58,107,169`,
  `backend/app/api/routers/accounts.py:146`). Behind the reverse proxy that is the **proxy's**
  address: nginx sets `X-Forwarded-For` (`infra/reverse-proxy/nginx.conf:34-35`), but nothing in
  the application reads it, and Gunicorn's own forwarded-header handling trusts only
  `127.0.0.1` by default, which the proxy container is not. Even the login rows therefore carry
  the proxy's address on a deployed stack.
- The mechanism: the address lives on the `Request`, and the services that write audit rows do
  not receive it. The same address rule is needed by PRB-029.

## Safety evaluation

Contributes to RISK-006 (incomplete audit trail).

## Resolution

Planned in CR-004: TASK-185 (one trusted-proxy rule for the originating client address,
SR-042 AC 1 to AC 3, [ADR-0019](../design/adr/0019-originating-client-address-trusted-proxy-rule.md)),
then TASK-137 (every request-caused audit row records it, SR-023 AC 6). Not yet fixed.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding D.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
