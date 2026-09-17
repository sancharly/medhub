---
id: "PRB-015"
type: problem-report
title: "Module list query is never invalidated, so DICOM gating goes stale"
status: open
criticality: major
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["correctness", "hazard:denial-of-care"]
---

# PRB-015 — Module list query is never invalidated, so DICOM gating goes stale

## Observed

`core/clinical/AttachmentItem.tsx:19` reads the `["myModules"]` query, which is never invalidated after an administrator changes module enablement — the UI keeps the old gating until a reload.

## Impact

SR-015 per-group module enablement is not reflected promptly: a viewer stays hidden after being enabled, or offered after being disabled.

## Safety evaluation

Contributes to RISK-004 (legitimate access wrongly denied).

## Resolution

TASK-144 (draft) — invalidate the module query on the mutations that change enablement.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding P.
