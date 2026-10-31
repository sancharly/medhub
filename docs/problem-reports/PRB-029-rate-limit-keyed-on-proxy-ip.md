---
id: "PRB-029"
type: problem-report
title: "Rate limiting is keyed on the proxy address"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-31"
criticality: minor
links: []
tags: ["security"]
---

# PRB-029 — Rate limiting is keyed on the proxy address

## Observed

`app/api/routers/anonymized_data.py` keys its rate limit on `request.client.host`, which behind the reverse proxy is the proxy itself, so every caller shares one bucket.

## Impact

The rate limit protects nothing per-caller and can lock out all users at once (SR-031, SR-024 retrieval path).

## Investigation

Read on 2026-10-31 (CR-004 Plan stage, Software Architect role). **Present as reported, plus two
defects in the counter.**

- `backend/app/api/routers/anonymized_data.py:66-67` keys the limit on `request.client.host`,
  which is the reverse proxy's address on a deployed stack (see PRB-010), or the string
  `"unknown"` when the client is missing. Every caller shares one bucket.
- The counter is not atomic: `_check_rate_limit` (`anonymized_data.py:29-39`) reads the count
  with `GET`, compares, then increments in a pipeline. Concurrent requests that all read 4 are
  all evaluated, so more than 5 attempts can be evaluated in a window.
- The window slides: `EXPIRE` is reset on every counted attempt (`anonymized_data.py:37-38`), so
  a caller who keeps trying is never released, and the window does not start at the first
  counted attempt as SR-042 AC 4 requires.

## Safety evaluation

Contributes weakly to RISK-007 (a shared bucket can deny legitimate retrieval).

## Resolution

Planned in CR-004: TASK-185 (originating client address, ADR-0019), then TASK-186 (count per
address, atomic increment, fixed 3600-second window from the first counted attempt, refusal
before the code is evaluated). Not yet fixed.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Low.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
