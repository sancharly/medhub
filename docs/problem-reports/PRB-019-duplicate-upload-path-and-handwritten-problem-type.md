---
id: "PRB-019"
type: problem-report
title: "Upload bypasses the shared request helper and `ProblemError` is hand-written in a generated file"
status: open
criticality: minor
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["correctness"]
---

# PRB-019 — Upload bypasses the shared request helper and `ProblemError` is hand-written in a generated file

## Observed

`frontend/src/api/client.ts:136-160` re-implements fetch and RFC 7807 handling instead of routing through `request<T>()` — and already lacks its 401→`AuthError` branch. `ProblemError` lives in `api/generated/types.ts:17`, a file whose header says it is generated and must not be hand-edited.

## Impact

Divergent error handling between upload and every other call, and a hand-written type that regeneration can clobber. Touches the SR-031 error contract.

## Safety evaluation

No hazard: failures surface as errors, not as wrong data.

## Resolution

TASK-143 (draft) — route upload through `request()` and move the override out of the generated file.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` findings M and N.
