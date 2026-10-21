---
id: "PRB-014"
type: problem-report
title: "Frontend mounts every route for any authenticated user"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
criticality: major
links: []
tags: ["security", "hazard:privacy"]
---

# PRB-014 — Frontend mounts every route for any authenticated user

## Observed

`frontend/src/app/App.tsx` mounts all routes for any authenticated user; only navigation links are role-filtered, so the backend 403 is the sole gate.

## Impact

Defense in depth for SR-005 and SR-009 is missing: a mistyped or shared URL renders an admin or clinical view shell to the wrong role before the API refuses.

## Safety evaluation

Contributes to RISK-001 (unauthorized disclosure) — the data itself is still protected server-side, which is why this is a hardening defect rather than a live leak.

## Resolution

TASK-142 (draft) — route-level role guards mirroring the backend policy.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding L.
