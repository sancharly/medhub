---
id: "PRB-029"
type: problem-report
title: "Rate limiting is keyed on the proxy address"
status: resolved
version: "1.2"
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

Fixed in CR-004 by TASK-185 (originating client address, ADR-0019) and TASK-186 (retrieval limit).
`POST /anonymized-data/retrieve` counts attempts under
`rate:anonymized_retrieve:{originating client address}`; the count is one atomic `INCR` plus
`EXPIRE 3600 NX` transaction, so the 3600-second window starts at the first counted attempt and is
not extended; the sixth attempt gets 429 before the code is evaluated; a missing peer is refused.
Reproduce: `cd backend && uv run pytest tests/api/test_anonymized_retrieve.py tests/core/test_client_address.py tests/api/test_client_address_middleware.py -v`
(TS-016 TC-016.1 to TC-016.5). Before the fix, client B was refused once client A used the shared
bucket, 10 concurrent attempts evaluated more than 5, and a caller who kept trying was never released.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Low.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
- 1.2 (2026-10-31) — TASK-186: Resolution written; status `open` → `resolved`. Closure follows the CR-004 close.
