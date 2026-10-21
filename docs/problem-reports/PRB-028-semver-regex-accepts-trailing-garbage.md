---
id: "PRB-028"
type: problem-report
title: "Module version regex accepts trailing garbage"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
criticality: minor
links: []
tags: ["security"]
---

# PRB-028 — Module version regex accepts trailing garbage

## Observed

`app/modules/discovery.py` — `_SEMVER_RE` is not fully anchored, so a version like `1.2.3-evil!` is accepted during module discovery.

## Impact

A module can declare a version the registry cannot compare meaningfully (SR-016); no code execution follows from it, since modules are trusted code at MVP.

## Safety evaluation

No hazard at MVP (ADR-0005: modules are reviewed, trusted code).

## Resolution

Not yet tracked by a task. Proposed: anchor the expression fully and reject on discovery. Needs a task and a CR.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Low.
