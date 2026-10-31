---
id: "PRB-028"
type: problem-report
title: "Module version regex accepts trailing garbage"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-31"
criticality: minor
links: []
tags: ["security"]
---

# PRB-028 — Module version regex accepts trailing garbage

## Observed

`app/modules/discovery.py` — `_SEMVER_RE` is not fully anchored, so a version like `1.2.3-evil!` is accepted during module discovery.

## Impact

A module can declare a version the registry cannot compare meaningfully (SR-016); no code execution follows from it, since modules are trusted code at MVP.

## Investigation

Read on 2026-10-31 (CR-004 Plan stage, Software Architect role). **Present as reported.**

- `backend/app/modules/discovery.py:13` compiles `^\d+\.\d+\.\d+` and `discovery.py:29` uses
  `.match`, which anchors only the start. `1.2.3-evil!`, `1.2.3.4` and `1.2.3 ` are accepted.
- No other check of the version follows; the registry stores the string as given.

## Safety evaluation

No hazard at MVP (ADR-0005: modules are reviewed, trusted code).

## Resolution

Planned in CR-004: TASK-200 (a fully anchored semantic-version expression, `fullmatch`, with
rejection cases). Not yet fixed.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Low.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
