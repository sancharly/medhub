---
id: "TASK-160"
type: task
title: "Point the smoke test's login check at the published proxy endpoint"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
links:
  - target: "SR-028"
    relation: implements
  - target: "TASK-155"
    relation: relates_to
tags: ["verification", "configuration-management", "cr:CR-001", "issue:sancharly/medhub#26"]
---

# TASK-160 — Point the smoke test's login check at the published proxy endpoint

- **Software item / unit:** SI-DEVINFRA `U-INF-Toolchain` (ADD-024); `infra/smoke-test.sh`
- **Depends on:** TASK-155 (pinned stack). Runs at Checkpoint A, before TASK-154.
- **Branch:** `bug/soup-pinning`
- **Resolves:** PRB-037 (added to CR-001 on 2026-10-22 by the human, who did not accept a 16/17
  smoke-test result as meeting AC-5)

## Objective

Check 9 of `infra/smoke-test.sh` posts to `http://localhost:8000/api/v1/auth/login`, a port the
Compose topology only `expose`s inside the `medhub` network, so the check can never pass on a
correctly started stack (PRB-037). Make the check exercise the published endpoint so that the
pinned stack passes the smoke test 17/17 and CR-001 AC-5 is met literally.

## Interfaces to honor

- `infra/docker-compose.yml`: only `reverse-proxy` publishes ports (80, 443). Do not publish the
  backend port to make the check pass — that would change the deployment topology.
- The development TLS certificate is self-signed; the check must not require a trusted CA.
- Keep the check's meaning: a migrated schema answers the login POST with 401/422, an empty schema
  with 500. Keep the "backend not running — skipping" branch for HTTP 000.

## Implementation detail

- In check 9, post to `https://localhost/api/v1/auth/login` through the reverse proxy with
  `curl -k` (self-signed certificate), or make the base URL a variable defaulting to that value.
- Follow the script's existing style for checks and messages; change nothing else in the script.
- Update the evidence in TASK-155 only by reference (this task's record holds the new run).

## Tests (write first)

- Run the current script against the started pinned stack and record check 9 failing (HTTP 000).

## Acceptance criteria

- [x] Check 9 targets the published proxy endpoint and passes on the started pinned stack (401/422)
- [x] `bash infra/smoke-test.sh` reports 17 passed, 0 failed on the pinned stack (CR-001 AC-5)
- [x] No change to `infra/docker-compose.yml` port publishing
- [x] PRB-037 is `resolved` per the problem-report-resolution body contract

## Verification

- `docker compose -f infra/docker-compose.yml up -d --build`
- `bash infra/smoke-test.sh` → 17 passed, 0 failed
- `docker compose -f infra/docker-compose.yml down` (never `-v`)
- `python3 infra/check_image_pins.py` still exits 0

## Definition of Done

- [x] Acceptance criteria met and evidence recorded below
- [x] PRB-037 `resolved`; CR-001 `resolves` → PRB-037 present
- [x] `traceability-check` shows no error for the touched records

## Implementation notes

- `infra/smoke-test.sh` check 9 (lines 124-143): the login POST now targets
  `https://localhost/api/v1/auth/login` through the reverse proxy, and `curl -s` became `curl -sk`
  (self-signed development certificate). A two-line comment above the check says why. Nothing else
  in the script changed (diff: +4/-2 lines in `infra/smoke-test.sh`). The 401/422 pass condition,
  the empty-status "skipping" branch and the failure message are untouched.
- `infra/docker-compose.yml` is unchanged: only `reverse-proxy` still publishes ports (80, 443).
- Observation, not changed: `curl -w "%{http_code}"` prints `000` when the connection fails, so the
  `[ "$LOGIN_STATUS" = "" ]` "backend not running - skipping" branch cannot be reached by an
  unreachable endpoint; a stopped stack falls to the final branch and reports `got HTTP 000`. The
  branch was kept as written, as the task requires ("change nothing else").
- Run-time observations that did not affect the result: the Compose warning
  `The "POSTGRES_PASSWORD" variable is not set` appeared (PRB-038; the existing `postgres_data`
  volume let PostgreSQL 16.15 start anyway); `createbuckets` exited 0 and the stack was up before
  the run (PRB-039 did not trigger). The backend log shows a Gunicorn
  `Control server error: [Errno 13] Permission denied: '/home/medhub'` at start-up; the API still
  answered normally. It was not investigated here.

## Evidence

Stack: `docker compose -f infra/docker-compose.yml up -d --build` on the reference workstation,
2026-10-22, pinned images (TASK-155), all services up, `infra-backend-1` serving. Cross-check:
`curl -sk -o /dev/null -w "%{http_code}" -X POST https://localhost/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"smoke@test.invalid","password":"unused"}'` returned `401`.

### Before (current script, test written first - check 9 fails)

`bash infra/smoke-test.sh` (exit 1):

```
=== MedHub Smoke Tests ===

-- Compose config --
  [PASS] docker-compose.yml is valid

-- Service topology --
  [PASS] service 'reverse-proxy' defined
  [PASS] service 'backend' defined
  [PASS] service 'frontend' defined
  [PASS] service 'postgres' defined
  [PASS] service 'redis' defined
  [PASS] service 'minio' defined
  [PASS] service 'celery-worker' defined

-- Port exposure (SR-008) --
  [PASS] only reverse-proxy publishes external ports (SR-008)

-- TLS / HTTPS redirect (SR-008) --
  [PASS] HTTP→HTTPS redirect configured
  [PASS] HSTS header configured (SR-008)
  [PASS] TLS 1.2+ enforced (SR-008)

-- At-rest encryption (SR-016) --
  [PASS] MinIO SSE-AES256 key configured (SR-016)

-- Data persistence --
  [PASS] named volume 'postgres_data' defined
  [PASS] named volume 'redis_data' defined
  [PASS] named volume 'minio_data' defined

-- Schema migration (SR-001.1, SR-003) --
  [FAIL] POST /auth/login returns non-500 (schema migrated): got HTTP 000 (expected 401/422; 500 = empty schema)

=== Results: 16 passed, 1 failed ===
exit=1
```

### After (check 9 through the proxy)

`bash infra/smoke-test.sh` (exit 0):

```
=== MedHub Smoke Tests ===

-- Compose config --
  [PASS] docker-compose.yml is valid

-- Service topology --
  [PASS] service 'reverse-proxy' defined
  [PASS] service 'backend' defined
  [PASS] service 'frontend' defined
  [PASS] service 'postgres' defined
  [PASS] service 'redis' defined
  [PASS] service 'minio' defined
  [PASS] service 'celery-worker' defined

-- Port exposure (SR-008) --
  [PASS] only reverse-proxy publishes external ports (SR-008)

-- TLS / HTTPS redirect (SR-008) --
  [PASS] HTTP→HTTPS redirect configured
  [PASS] HSTS header configured (SR-008)
  [PASS] TLS 1.2+ enforced (SR-008)

-- At-rest encryption (SR-016) --
  [PASS] MinIO SSE-AES256 key configured (SR-016)

-- Data persistence --
  [PASS] named volume 'postgres_data' defined
  [PASS] named volume 'redis_data' defined
  [PASS] named volume 'minio_data' defined

-- Schema migration (SR-001.1, SR-003) --
  [PASS] POST /auth/login returns non-500 (schema migrated)

=== Results: 17 passed, 0 failed ===
exit=0
```

- `python3 infra/check_image_pins.py` -> exit 0.
- `docker compose -f infra/docker-compose.yml down` (no `-v`) -> containers and network removed;
  volumes `infra_postgres_data`, `infra_redis_data`, `infra_minio_data` kept.

## QA review (2026-10-22)

**Verdict: APPROVED** (`in_review → approved`). No CRITICAL or HIGH finding. CR-001 AC-5 is met
literally: 17 passed, 0 failed on the pinned stack, run by QA. The only change is check 9. Port
publishing in Compose is unchanged.

### Findings

- **[MEDIUM] CR-001 v1.3 adds PRB-037 and TASK-160 only in some sections.** The frontmatter, AC-17,
  the plan table, the "Scope change at Checkpoint A" paragraph and the version history are
  updated. Four sections still describe the 1.2 scope:
  - "Reason" lists PRB-001, PRB-002, PRB-033 and TASK-154 (`CR-001…md:48-59`), without PRB-037.
  - "In scope" has no item for the smoke-test fix, and item 8 "Records" (`:89`) still says
    "PRB-001, PRB-002 and PRB-033 move to `resolved`".
  - The §7.4 change analysis says it covers "the four changes of the Scope" (`:137`), and its table
    (`:148-154`) has no TASK-160 row. `risk-management` requires recording the §7.4.1 answer even
    when it is "no impact".
  - In the plan table, TASK-154's "Depends on" (`:346`) omits TASK-160, although `:375` says
    TASK-160 runs before TASK-154.

  → Add PRB-037 (minor) to "Reason". Add a scope item 9, "Smoke test login check (PRB-037)", and add
  PRB-037 to item 8. Add a change-analysis row along these lines: `infra/smoke-test.sh` is
  verification tooling that does not ship and changes no product, configuration or control; no
  hazard contribution; no control affected; verified by the AC-5 smoke run. Change ":137" to
  "five changes". Add TASK-160 to TASK-154's "Depends on". This is an orchestrator record, so it does
  not block TASK-160, but it must be fixed before TASK-159 checks AC-18.
- **[LOW] PRB-037 `## Source` is stale.** `PRB-037…md:90` says "out of scope for CR-001", but CR-001
  `resolves` it. → Change it to: "…; initially left out of CR-001, added to its scope at Checkpoint
  A (2026-10-22, CR-001 1.3)."

### The developer's two observations — PRB recommendation

- **(a) The dead "backend not running — skipping" branch: no new PRB.**
  - Confirmed: `curl -w "%{http_code}"` prints `000` when the connection fails, and the branch tests
    for `""` (`infra/smoke-test.sh:138`). QA ran the script against the stopped stack and got
    `[FAIL] … got HTTP 000`, 16/1, exit 1.
  - Even if the branch were reached, it calls `check` with a non-`ok` result, which counts as FAIL
    (`smoke-test.sh:28-37`). Either way a stopped stack fails, so the check never gives a false pass.
    Only the message is less helpful.
  - The defect is already recorded in PRB-037's Investigation ("tests for an empty string, which
    `curl -w` never produces"), and it is the same check and the same defect. Folding it in there is
    enough.
  - Optional cleanup, as a one-line change under PRB-037 or later: test for `"000"` and report "stack
    not reachable (run after docker compose up)" as the FAIL text.
  - This task's "Interfaces to honor" says the branch is "for HTTP 000". That was a wrong premise;
    the developer correctly kept the code unchanged and recorded it.
- **(b) Gunicorn `Control server error: [Errno 13] Permission denied: '/home/medhub'`: real. Raise
  PRB-041 (minor).**
  - Confirmed from the logs: it appears once per start, right after `Starting gunicorn 26.0.0` and
    `Booting worker`.
  - Mechanism: `backend/Dockerfile:18` runs `useradd -r` with no `-m`, so `HOME=/home/medhub` does
    not exist and `/home` is `root:root 755`.
  - Gunicorn ≥ 25.1.0 starts a control socket by default at `$XDG_RUNTIME_DIR/gunicorn.ctl`, falling
    back to `$HOME/.gunicorn/gunicorn.ctl` (gunicorn `config.py` `_get_default_control_socket`). It
    cannot create the parent directory, so the control-server thread dies (`ctl/server.py:184`).
  - Effect: the `gunicornc` runtime-management interface (worker status, worker count, graceful
    reload) is unavailable. The workers are unaffected: the API answered 401 through the proxy.
    Nothing in the repository uses `gunicornc`.
  - No data-integrity, safety or clinical impact. But an ERROR line on every normal start trains
    operators to ignore errors in the backend log, which RISK-007's monitoring control relies on.
    The interface also starts by default without having been considered.
  - Recommended fix: add `--no-control-socket` to the `gunicorn` command in `backend/entrypoint.sh`.
    MedHub does not use the interface, and disabling it removes an unused management surface.
    Creating the home directory instead (`useradd -r -m`) is the weaker alternative.
  - Pre-existing: CR-001 did not change Gunicorn's version.
  - Input for TASK-154: SOUP-005 (Gunicorn 26.0.0) should note the default-on control socket.
  - The human decides whether PRB-041 joins CR-001 or stays outside it, as PRB-038 and PRB-039 do.

Observations (no action needed):
- No TS cites `infra/smoke-test.sh`. The AC-5 evidence lives in TASK-155 and in this task, and goes
  into the release TR, as CR-001's "Verification approach" says.
- The Compose warning `POSTGRES_PASSWORD is not set` appeared again (PRB-038), and `createbuckets`
  started without incident (PRB-039 did not trigger). Both are known.

### Verification run (QA, 2026-10-22, reference workstation, Docker)

| Command | Result |
|---|---|
| `git diff --stat` | only `infra/smoke-test.sh` (+4/−2, check 9: URL, `-sk`, two comment lines), PRB-037 and CR-001. `git diff infra/docker-compose.yml` is empty. Only `reverse-proxy` has `ports:` (80, 443); `backend` has `expose: "8000"` |
| PRB-037 line references | `docker-compose.yml:21-23` and `:40-41`, `nginx.conf:31-32`, HEAD `smoke-test.sh:131/:136/:138-139`: all accurate |
| `docker compose -f infra/docker-compose.yml up -d --build` | exit 0. Running images: nginx `1.31.8-alpine@sha256:e2d9…`, postgres `16.15@sha256:9e2c…`, redis `7.4.11-alpine@sha256:8920…`, minio `RELEASE.2025-09-07T16-13-09Z@sha256:14ce…`. Proxy probe `curl -sk … POST https://localhost/api/v1/auth/login` → `401` |
| `bash infra/smoke-test.sh` (fixed) | `[PASS] POST /auth/login returns non-500 (schema migrated)`, **17 passed, 0 failed**, exit 0 |
| HEAD version of the script (`git show HEAD:infra/smoke-test.sh`, run as a temporary file in `infra/`, deleted straight after) | `[FAIL] … got HTTP 000`, 16 passed, 1 failed, exit 1 |
| `docker logs infra-backend-1`; `docker exec … id`, `ls -ld /home /home/medhub`; Gunicorn source in the image | see (b) above |
| `docker compose -f infra/docker-compose.yml down` (no `-v`) | containers and network removed; `infra_postgres_data`, `infra_redis_data` and `infra_minio_data` kept |
| `bash infra/smoke-test.sh` with the stack stopped | `[FAIL] … got HTTP 000`, 16/1, exit 1. Observation (a) confirmed |
| `python3 infra/check_image_pins.py` | exit 0 |
| `traceability-check` (fallback parser) on TASK-160, PRB-037, CR-001, against all 330 records | **0 errors, 0 warnings.** E9 holds for PRB-037 (CR-001 `resolves`). TASK-160 `implements` SR-028 (E8) |
| PRB-037 body contract | Investigation has `file:line` references and the mechanism. Safety evaluation covers data integrity, safety function and clinical decision, confirms `minor`, and states no release and no notification. Resolution lists the files, the rationale and reproducible steps, and states what was not tested (the 500 branch) |
