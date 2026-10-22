---
id: "PRB-037"
type: problem-report
title: "Smoke test login check targets a port the stack does not publish"
status: resolved
version: "1.1"
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

## Investigation

Root cause: check 9 was written against an address the Compose topology never publishes.
`infra/smoke-test.sh:131` (before the fix) posted to `http://localhost:8000/api/v1/auth/login`.
In `infra/docker-compose.yml` only `reverse-proxy` has `ports:` (lines 21-23, 80 and 443); `backend`
uses `expose: "8000"` (lines 40-41), which is reachable only from inside the `medhub` network. A
`curl` from the host to `localhost:8000` therefore gets no connection and `-w "%{http_code}"`
prints `000`, which falls through to the final `else` at `infra/smoke-test.sh:138-139` and is
reported as `[FAIL]`. The "skipping" branch at `infra/smoke-test.sh:136` tests for an empty string,
which `curl -w` never produces, so it did not help. The proxy forwards `/api/` to `backend:8000`
(`infra/reverse-proxy/nginx.conf:31-32`) over TLS on 443, so the endpoint the stack actually
publishes is `https://localhost/api/v1/auth/login`. The check was most likely written when the
backend port was thought to be published, and it was never run against the finished topology
(TASK-004 introduced the reverse-proxy-only exposure that check 3 verifies).

## Safety evaluation

- Data integrity: not affected. The defect is in verification tooling; the product, its data and
  its configuration are unchanged by the defect and by the fix.
- Safety-related function / clinical decision: not affected. No software function or clinical
  output depends on `infra/smoke-test.sh`.
- Criticality `minor`: confirmed. The effect was a false failure of a deployment check (a missed
  signal, not a wrong result in the product), and the runtime check it carried, a migrated schema,
  was never exercised until now. That gap matters for verification evidence (CR-001 AC-5), not for
  hazards. The fix makes the check able to fail for the right reason: a 500 from an empty schema.
- Released versions: no `release` record exists in `docs/releases/`, so no released version is
  affected and no notification is needed.

## Resolution

Changed `infra/smoke-test.sh` (check 9, lines 124-143): the login POST now goes to
`https://localhost/api/v1/auth/login` through the reverse proxy, with `curl -sk` because the
development certificate is self-signed, plus a two-line comment saying why. The 401/422 pass
condition, the empty-status skipping branch and the failure message are unchanged, and nothing else
in the script changed. `infra/docker-compose.yml` is unchanged: the backend port is still not
published. Chosen over running the request inside the `backend` container because the proxy path
checks the topology an operator actually uses and needs no `exec` into the stack. Implemented by
TASK-160, resolved by CR-001.

Verification (reproducible, reference workstation, 2026-10-22, pinned stack from TASK-155):

1. `docker compose -f infra/docker-compose.yml up -d --build`
2. Before the fix: `bash infra/smoke-test.sh` -> `[FAIL] POST /auth/login returns non-500 (schema
   migrated): got HTTP 000 ...`, `16 passed, 1 failed`, exit 1.
3. After the fix: `bash infra/smoke-test.sh` -> `[PASS] POST /auth/login returns non-500 (schema
   migrated)`, `17 passed, 0 failed`, exit 0. The same POST returned HTTP 401.
4. `docker compose -f infra/docker-compose.yml down` (no `-v`); `python3 infra/check_image_pins.py`
   -> exit 0.

Full output of both runs is in TASK-160 (Evidence). Not tested: the 500 branch (an empty schema);
the check was not run against a database without migrations.

## Source

Found by the software developer while running TASK-155 verification (AC-5). Added to CR-001's
scope at Checkpoint A by the human (2026-10-22, CR-001 1.3); resolved by TASK-160.
