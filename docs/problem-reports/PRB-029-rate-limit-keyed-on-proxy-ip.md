---
id: "PRB-029"
type: problem-report
title: "Rate limiting is keyed on the proxy address"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
criticality: minor
links: []
tags: ["security"]
---

# PRB-029 — Rate limiting is keyed on the proxy address

## Observed

`app/api/routers/anonymized_data.py` keys its rate limit on `request.client.host`, which behind the reverse proxy is the proxy itself, so every caller shares one bucket.

## Impact

The rate limit protects nothing per-caller and can lock out all users at once (SR-031, SR-024 retrieval path).

## Safety evaluation

Contributes weakly to RISK-007 (a shared bucket can deny legitimate retrieval).

## Resolution

Not yet tracked by a task. Proposed: trust `X-Forwarded-For` only from the known proxy and key on the client address. Needs a task and a CR; coordinate with TASK-137, which needs the same client address.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Low.
