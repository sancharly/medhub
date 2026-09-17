---
id: "PRB-024"
type: problem-report
title: "Group membership lookup issues one query per membership"
status: open
criticality: minor
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["performance"]
---

# PRB-024 — Group membership lookup issues one query per membership

## Observed

`app/groups/service.py:132` — `groups_of` calls `get()` per membership row instead of a single `IN` query.

## Impact

Latency grows with membership count on a path used by module gating (SR-014, SR-015, SR-026).

## Safety evaluation

No hazard beyond the general latency contribution in RISK-007.

## Resolution

Not yet tracked by a task. Proposed: a single `IN` query. Needs a task and a CR.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Performance.
