---
id: "PRB-023"
type: problem-report
title: "Concurrent-session cap eviction is not atomic"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
criticality: major
links: []
tags: ["correctness", "hazard:security"]
---

# PRB-023 — Concurrent-session cap eviction is not atomic

## Observed

`app/auth/session.py:97` implements the concurrency cap as a multi-step read-then-write sequence against Redis with no transaction, so two simultaneous logins can both pass the cap or evict the wrong session.

## Impact

The SR-030 concurrent-session limit is not reliably enforced.

## Safety evaluation

Contributes to RISK-005 (account takeover: an attacker session survives an eviction meant to remove it).

## Resolution

Not yet tracked by a task. Proposed: perform the cap check and eviction in a Lua script or a `MULTI`/`EXEC` pipeline. Needs a task and a CR.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Performance.
