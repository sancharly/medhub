---
id: "PRB-037"
type: problem-report
title: "Smoke test login check targets a port the stack does not publish"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
criticality: minor
links: []
tags: ["verification", "infrastructure"]
---

# PRB-037 — Smoke test login check targets a port the stack does not publish

## Observed

Check 9 of `infra/smoke-test.sh` ("POST /auth/login returns non-500 (schema migrated)") posts to
`http://localhost:8000/api/v1/auth/login`. In `infra/docker-compose.yml` only `reverse-proxy`
publishes ports (80, 443); `backend` uses `expose: 8000`, which is internal to the `medhub` network.
On a correctly started stack the request therefore gets no response (`curl` reports HTTP 000) and
the script reports `[FAIL]` and exits 1, whatever the state of the schema.

Observed on 2026-10-22 on the reference workstation, on the unpinned (pre-CR-001) stack and again on
the pinned stack: 16 passed, 1 failed, the failure being this check. The same request through the
proxy (`POST https://localhost/api/v1/auth/login`, `-k`) returns HTTP 401, i.e. the schema is
migrated and the auth layer is active.

## Impact

- `infra/smoke-test.sh` cannot pass against the Compose topology it documents, so its result carries
  no signal and CR-001 AC-5 ("passes `infra/smoke-test.sh`") cannot be met literally.
- The one runtime check in the script (migrated schema) is never exercised.

## Safety evaluation

No hazard is realized: the defect is in verification tooling, not in the product. Hence `minor`.

## Proposed resolution

Point check 9 at the published endpoint (`https://localhost/api/v1/auth/login` with `curl -k`, since
the development certificate is self-signed), or run it inside the `backend` container. Needs a task.

## Source

Found by the software developer while running TASK-155 verification (AC-5); out of scope for CR-001.
