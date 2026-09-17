---
id: "PRB-010"
type: problem-report
title: "Authorization and consent audit records carry no source IP"
status: open
criticality: major
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["security", "hazard:detectability"]
---

# PRB-010 — Authorization and consent audit records carry no source IP

## Observed

`authz/service.py:71,80` writes audit rows with `ip=None`; only the login, logout and password flows capture the source address.

## Impact

SR-023 requires security-relevant events to be reconstructable; without the origin, a wrong access cannot be attributed.

## Safety evaluation

Contributes to RISK-006 (incomplete audit trail).

## Resolution

TASK-137 (draft) — thread the request context into the authorization service and record the client IP, taking the proxy header into account (see PRB-029).

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding D.
