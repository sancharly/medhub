---
id: "PRB-022"
type: problem-report
title: "Activation token validation scans the whole account table"
status: open
criticality: major
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["performance"]
---

# PRB-022 — Activation token validation scans the whole account table

## Observed

`app/identity/activation.py` validates and activates by calling `repo.list()` and scanning in Python, an O(n) operation per attempt.

## Impact

Activation latency grows with the user base and the endpoint becomes an easy amplification target (SR-033, SR-026).

## Safety evaluation

Contributes to RISK-007 and, indirectly, RISK-009 (a patient cannot activate their account).

## Resolution

Not yet tracked by a task. Proposed: an indexed lookup on `activation_token_hash`. Needs a task and a CR.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Performance.
