---
id: "PRB-026"
type: problem-report
title: "Role-based authorization is embedded in the persistence layer"
status: open
criticality: major
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["correctness", "hazard:privacy"]
---

# PRB-026 — Role-based authorization is embedded in the persistence layer

## Observed

`app/db/repositories/appointment_repo.py:29` — `list_for_actor` branches on the actor's role inside the repository, so an authorization decision lives outside `AuthorizationService`, against ADR-0006's single decision point.

## Impact

SR-005 deny-by-default is evaluated in two places, so the two can diverge; the repository decision is not audited.

## Safety evaluation

Contributes to RISK-001 (unauthorized disclosure) and RISK-006 (an unaudited decision).

## Resolution

Not yet tracked by a task. Proposed: move the scoping into the service/authz layer and have the repository take an explicit filter. Needs a task and a CR.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Simplicity / hygiene.
