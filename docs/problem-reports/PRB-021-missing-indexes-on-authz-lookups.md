---
id: "PRB-021"
type: problem-report
title: "Authorization lookups have no supporting indexes"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
criticality: major
links: []
tags: ["performance", "hazard:availability"]
---

# PRB-021 — Authorization lookups have no supporting indexes

## Observed

`app/db/alembic/versions/0001_initial.py` creates no index on `appointment.scheduled_at`, `consent_grant.appointment_id`, `clinical_entry.patient_id` or `attachment.patient_id` — all of which are read on every authorization decision.

## Impact

Every clinical request degrades as data grows, against the SR-026 budgets.

## Safety evaluation

Contributes to RISK-007 (clinical information unavailable, through latency).

## Resolution

Not yet tracked by a task. Proposed: an Alembic migration adding the four indexes, with a query plan check in the performance task (TASK-112).

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Performance.
