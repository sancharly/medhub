---
id: "PRB-020"
type: problem-report
title: "No route-level code splitting, so the bundle cannot absorb the DICOM viewer"
status: open
criticality: minor
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["performance"]
---

# PRB-020 — No route-level code splitting, so the bundle cannot absorb the DICOM viewer

## Observed

`app/App.tsx` imports every route statically; there is no `React.lazy` anywhere, so the single bundle will have to carry Cornerstone3D once the viewer lands.

## Impact

SR-026 performance budgets and SR-020 responsiveness on slower devices are at risk once the viewer module exists.

## Safety evaluation

No hazard today; the viewer is not implemented yet.

## Resolution

TASK-145 (draft) — route-based code splitting with lazy module chunks.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding S.
