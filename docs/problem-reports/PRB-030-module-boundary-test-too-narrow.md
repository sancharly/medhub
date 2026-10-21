---
id: "PRB-030"
type: problem-report
title: "Module boundary test denies only two import substrings"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
criticality: minor
links: []
tags: ["verification"]
---

# PRB-030 — Module boundary test denies only two import substrings

## Observed

`backend/app/modules/.../test_module_boundary.py` asserts against two import substrings, so a module importing most `app.*` internals would pass.

## Impact

The architectural boundary behind SR-016 and ADR-0005 is only nominally verified.

## Safety evaluation

No direct hazard; it weakens the verification of the module isolation claim.

## Resolution

Not yet tracked by a task. Proposed: deny every `app.*` import except the module contract, deps, errors and audit surfaces. Needs a task and a CR.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Low.
