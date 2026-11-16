---
id: "PRB-092"
type: problem-report
title: "Upload scratch space in the API container is neither limited nor checked"
status: resolved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-11-15"
updated: "2026-11-16"
criticality: minor
links: []
tags: ["reliability", "deployment", "found-in:TASK-225", "outside:CR-006"]
---

# PRB-092 — Upload scratch space in the API container is neither limited nor checked

## Observed

Found by QA in the TASK-225 review (2026-11-15). Starlette's form parsing spools a file part above 1 MiB to a temporary file in the API container (ADR-0021). The attachment maximum is 150 MiB, so several concurrent maximum-size uploads need that much free disk in the container's temporary directory. Neither `backend/app` nor `infra/docker-compose.yml` limits the number of concurrent uploads, sizes or mounts a volume or `tmpfs` for that directory, or checks the free space; `infra/DEPLOY.md` states only that the space is needed. CR-006's plan listed the risk and left it to the documentation.

## Impact

When the temporary directory in the API container is full, the upload fails and nothing is stored: no object-store write and no database row for the failed upload (RISK-007, clinical information unavailable for that upload). Found behaviour (before TASK-232, `4eeef74`): FastAPI wraps the spool `OSError` raised inside `await request.form()` into a plain HTTP 400 "There was an error parsing the body" (`application/json`, not a problem), and the API does not log it, so neither the user nor the operator could tell it from a bad request (TASK-231 QA R1-1; `fastapi/routing.py:420-465`, which keeps the 500 handler at `backend/app/api/errors.py:206-221` from running). The reverse proxy also buffers the body in its own client-body temporary directory (`infra/reverse-proxy/nginx.conf:75-89` leaves `client_body_temp_path` at its default, `/var/cache/nginx/client_temp` in the pinned `nginx:alpine` image); when that is full nginx answers its own 500 and logs at `crit` (R1-2). Other requests that need the same directory may fail too while it is full.

## Investigation

ADR-0021 chose to keep Starlette's spooling (option 1) over a streaming parser; its consequences name the bounded memory but not the disk. `grep` for spool, tempfile and disk in `backend/app` and Compose finds no limit or check. A deployment's free space depends on the host and image layer, which this repository does not set. Mechanism of the wrong answer: the route takes `file: UploadFile` (`backend/app/api/routers/attachments.py:105`), so the multipart parse runs before the handler; FastAPI turns any exception from it into a 400, so the `OSError` was neither logged nor a 5xx.

## Safety evaluation

No safety-related function or clinical decision is affected; no stored data is changed or lost, and the user can repeat the upload. Found behaviour: the failure was visible to the user only as a generic 400 and silent for the operator (no API log), so it could be mistaken for a client error. After TASK-232 it is logged at ERROR and answered 503 with a retry instruction (see Resolution). The capacity cause remains and contributes to RISK-007 (information unavailable). Criticality `minor`. Outside CR-006. Decision: CR-007 D-1 (no capacity control, residual accepted), D-7 (code fix) and D-8 (resolved by CR-007, sizing 300 MiB); the residual acceptance is the human's, in MedTrace.

## Resolution

Resolved by CR-007 (D-7, D-8) in two parts, both verified by QA:

1. **Failure handling (TASK-232, commit `99c208a`).** `backend/app/api/routers/attachments.py:34-68` maps a 400 whose `__cause__` is an `OSError` on the upload route to `UploadStorageUnavailableProblem` (`backend/app/api/errors.py:163-179`): 503 `application/problem+json` `upload-storage-unavailable` with `Retry-After: 30`, after one ERROR log line with the HTTP method, the route template and the errno (no path, file name or clinical data). Nothing is stored; a malformed body still answers 400. Verified by TS-007 TC-007.17 (`backend/tests/api/test_attachments_router.py::TestUploadScratchSpaceFailure`) and TS-011 TC-011.7 (the upload form shows the 503 detail).
2. **Sizing and operator information (TASK-231).** `infra/DEPLOY.md` ("Attachment size") names both directories (the API container's `/tmp` unless `TMPDIR` is set; the proxy's nginx client-body directory), sizes them at about 300 MiB free per concurrent maximum-size upload where they share a disk (about 150 MiB in each otherwise), says to monitor the free space, and states the 503 behaviour and the proxy's own 500.

Not changed, by decision (D-1): no capacity control (concurrency limit, sized volume or start-up free-space check), so the space can still run out; this residual is accepted in RISK-007 (1.20, `in_review`, 3 × 2 alarp unchanged) and listed in arc42 section 11. No Compose or nginx change.

**QA confirmation (2026-11-16, TASK-231 round 2):** on `99c208a` a spool `OSError(ENOSPC)` through
`create_app()` answers 503 `upload-storage-unavailable` with `Retry-After: 30` and stores nothing (TASK-232 approved,
TC-007.17, TC-011.7); the pinned `nginx:1.31.8-alpine` buffers to `/var/cache/nginx/client_temp` and, with that
directory full, answers 500 and logs at `crit`, as `infra/DEPLOY.md` states. TASK-231 approved.

## Version history

- 1.0 (2026-11-15) — Created from the TASK-225 QA review. `open`.
- 1.1 (2026-11-16) — CR-007 TASK-231 round 1: Resolution states the accepted residual and the DEPLOY.md measure. Stays `open`.
- 1.2 (2026-11-16) — CR-007 TASK-231 round 2 (QA R1-1 to R1-3): Impact, Investigation and Safety evaluation corrected for the behaviour before TASK-232 (an unlogged 400, not a 5xx); the proxy buffer added; "Open decision for a human" replaced by the CR-007 decisions; Resolution covers TASK-232 and the sizing. Stays `open` until QA confirms; then `resolved` (D-8).
- 1.3 (2026-11-16, QA) — TASK-231 round 2 approved: QA confirmation added; Resolution no longer says "in the working tree". `resolved` (CR-007 D-8).
