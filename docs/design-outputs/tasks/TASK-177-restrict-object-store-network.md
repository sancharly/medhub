---
id: "TASK-177"
type: task
title: "Restrict the object store to the backend and the bucket initialiser"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "SR-040"
    relation: implements
  - target: "RISK-012"
    relation: mitigates
  - target: "RISK-001"
    relation: mitigates
  - target: "CR-002"
    relation: relates_to
  - target: "PRB-043"
    relation: relates_to
  - target: "TASK-176"
    relation: relates_to
tags: ["security", "network", "cr:CR-002", "issue:sancharly/medhub#33", "control:design"]
---

# TASK-177 — Restrict the object store to the backend and the bucket initialiser

- **Software item / unit:** SI-OBJSTORE `U-OBJ-Server` (ADD-025), deployment topology
- **Depends on:** TASK-176 (`relates_to`)
- **Branch:** `bug/minio-object-store`
- **Size:** S (Compose, smoke test, TS-014)
- **Needs:** a Docker host

## Objective

SR-040 AC 3. Only `backend` and `object-store-init` can reach the object store. Every other
service is refused, and nothing is published to the host. An actor with a foothold in any other
container can no longer reach the store (RISK-012).

## Interfaces to honor

- Add a network `object-store` with `internal: true`. The store needs no egress.
  - `object-store` and `object-store-init` join it only.
  - `backend` joins `medhub` and `object-store`.
  - `reverse-proxy`, `frontend`, `postgres`, `redis` and `celery-worker` stay on `medhub` only.
  - `object-store-preflight` keeps `network_mode: none`.
- Confirm CR-002 A-2 first: `celery-worker` never uses the object store
  (`grep -rn "ObjectStorageClient\|object_storage" backend/app/workers`). If it does, stop and
  report.
- Docker cannot publish a port from a container that is only on an `internal` network. The CI
  override of TASK-179 must therefore attach the store to a CI-only network as well. Record that
  in TS-014.

## Implementation detail

1. Make the Compose changes above.
2. Extend `infra/smoke-test.sh` with a started-stack section that is skipped, with a message,
   when the stack is not running, as the login check already is:
   - for each of `reverse-proxy`, `frontend`, `postgres`, `redis` and `celery-worker`: a
     connection attempt from inside the container to `object-store:<s3 port>` fails, because the
     name does not resolve or the connection is refused. Use a tool present in each image
     (`getent`, `nc`, `python` or bash `/dev/tcp`), and document the one chosen per image;
   - from `backend`: `ObjectStorageClient().put_object` and `get_object` round trip a test object,
     which is then deleted;
   - from the host: no port of the store is published (`docker compose port` is empty, and
     `docker inspect` shows no `HostPort`).
3. **TS-014** TC-014.6: the network membership assertions (static, from
   `docker compose config --format json`) and the started-stack checks above.

## Acceptance criteria

- [ ] CR-002 **AC-3** / SR-040 AC 3: the store joins a network that only the backend and the
      initialiser join, and publishes no host port. Connections from the proxy, frontend,
      PostgreSQL, Redis and worker containers are refused. The backend can write and read an
      object.
- [ ] SR-040 AC 5: verified against the deployment definition and a started stack.

## Verification

```sh
python3 -m unittest discover -s infra/tests -v
docker compose -f infra/docker-compose.yml up -d && bash infra/smoke-test.sh     # all checks pass, count recorded
```

Also an attachment upload and download through `https://localhost`, as in TASK-161 step 5, using
a test account created and removed for the run.

## Definition of Done

- [ ] Infrastructure tests and smoke pass. The backend suite passes.
- [ ] `traceability-check` shows no error for this task and TS-014.
