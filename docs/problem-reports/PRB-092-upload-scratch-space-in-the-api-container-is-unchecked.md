---
id: "PRB-092"
type: problem-report
title: "Upload scratch space in the API container is neither limited nor checked"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-15"
updated: "2026-11-15"
criticality: minor
links: []
tags: ["reliability", "deployment", "found-in:TASK-225", "outside:CR-006"]
---

# PRB-092 — Upload scratch space in the API container is neither limited nor checked

## Observed

Found by QA in the TASK-225 review (2026-11-15). Starlette's form parsing spools a file part above 1 MiB to a temporary file in the API container (ADR-0021). The attachment maximum is 150 MiB, so several concurrent maximum-size uploads need that much free disk in the container's temporary directory. Neither `backend/app` nor `infra/docker-compose.yml` limits the number of concurrent uploads, sizes or mounts a volume or `tmpfs` for that directory, or checks the free space; `infra/DEPLOY.md` states only that the space is needed. CR-006's plan listed the risk and left it to the documentation.

## Impact

When the temporary directory is full, an upload fails with a server error (RISK-007, clinical information unavailable for that upload). No stored data is changed: nothing is written to the object store or the database for a failed upload. Other requests that need the same directory may fail too while it is full.

## Investigation

ADR-0021 chose to keep Starlette's spooling (option 1) over a streaming parser; its consequences name the bounded memory but not the disk. `grep` for spool, tempfile and disk in `backend/app` and Compose finds no limit or check. A deployment's free space depends on the host and image layer, which this repository does not set.

## Safety evaluation

No safety-related function or clinical decision is affected; the failure is loud (a 5xx on the upload) and leaves no partial record. Contributes to RISK-007 (information unavailable). Criticality `minor`. Outside CR-006.

**Open decision for a human:** accept the residual with the DEPLOY.md note, or add a control (a mounted scratch volume of a stated size, an upload concurrency limit, or a free-space check at start-up).

## Resolution

Not fixed here. The residual is listed in arc42 section 11 and cites this record.
