---
id: "PRB-008"
type: problem-report
title: "Attachment upload and download buffer the whole object in memory"
status: open
criticality: major
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["performance", "hazard:availability"]
---

# PRB-008 — Attachment upload and download buffer the whole object in memory

## Observed

`api/routers/attachments.py` awaits `file.read()` into memory before the size check, and the download path loads the whole object then re-chunks it from RAM.

## Impact

Concurrent large DICOM transfers exhaust process memory and blow the SR-026 performance budget; the size limit is enforced after the damage.

## Safety evaluation

Contributes to RISK-007 (clinical information unavailable).

## Resolution

TASK-135 (draft) — stream on both directions and enforce the limit while streaming.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding A.
