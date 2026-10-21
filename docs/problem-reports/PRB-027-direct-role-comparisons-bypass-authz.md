---
id: "PRB-027"
type: problem-report
title: "Identity services compare roles directly instead of asking the authorization service"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
criticality: major
links: []
tags: ["correctness", "hazard:privacy"]
---

# PRB-027 — Identity services compare roles directly instead of asking the authorization service

## Observed

`app/identity/account_service.py` and `app/identity/lifecycle.py` compare `user_type` directly rather than calling `AuthorizationService`, bypassing the single decision point required by ADR-0006.

## Impact

Same divergence and audit gap as PRB-026, on the account lifecycle paths (SR-032, SR-034).

## Safety evaluation

Contributes to RISK-001 and RISK-006.

## Resolution

Not yet tracked by a task. Proposed: route those checks through the authorization service so every decision is centralized and audited. Needs a task and a CR.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Simplicity / hygiene.
