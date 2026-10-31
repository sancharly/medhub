---
id: "TASK-198"
type: task
title: "Run the frontend image as a non-root user and check every built image's UID"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
links:
  - target: "SR-041"
    relation: implements
  - target: "RISK-001"
    relation: mitigates
  - target: "PRB-007"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "ADD-026"
    relation: relates_to
  - target: "ADD-018"
    relation: relates_to
tags: ["security", "deployment", "cr:CR-004", "control:design"]
---

# TASK-198 — Run the frontend image as a non-root user and check every built image's UID

- **Software item / unit:** SI-DEPLOY `U-DEP-RuntimeUsers` (ADD-026).
- **PRB:** PRB-007 (root container). **CR:** CR-004.
- **Depends on:** TASK-203 (Compose file edited first). Independent of the backend code tasks.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (`frontend/Dockerfile`, `frontend/nginx.conf`, `infra/reverse-proxy/nginx.conf`,
  `infra/smoke-test.sh`, 1 new infra test; TS-015)
- **Needs:** a Docker host (image builds, started stack).

## Objective

SR-041 AC 1 and AC 6: every image MedHub builds runs its main process with UID ≠ 0, checked on
the image configuration and on the running process. PRB-007 Investigation: the backend image
already has `USER medhub` (`backend/Dockerfile:18-19`); the frontend image (`nginx:1.31.8-alpine`)
runs as root on port 80.

## Implementation detail

- `frontend/Dockerfile`: keep the pinned `nginx` image (no new SOUP); set `USER nginx` (the
  image's UID 101); make `/var/cache/nginx`, `/var/run` (or `pid /tmp/nginx.pid`) and the temp
  paths writable by it.
- `frontend/nginx.conf`: `listen 8080`.
- `infra/reverse-proxy/nginx.conf:46`: `proxy_pass http://frontend:8080`; Compose `expose: "8080"`.
- `infra/smoke-test.sh`: for `backend`, `celery-worker`, `frontend` (and the one-shot services
  from the backend image, by `docker inspect` of the image) check `Config.User` is non-empty and
  not `root`/`0`, and `docker compose exec <svc> id -u` ≠ 0 for the running ones; the SPA loads
  through the proxy.

## Tests (write first)

- `infra/tests/test_images_non_root.py`: parse `backend/Dockerfile` and `frontend/Dockerfile`;
  the last stage has a `USER` that is not root; the frontend listens on an unprivileged port and
  the proxy targets it.
- `infra/smoke-test.sh` (started stack): image `Config.User` and running-process UID checks; the
  index page through the proxy returns 200.

## Acceptance criteria

- [ ] SR-041 AC 1: image configuration non-root for every built image
      (`infra/tests/test_images_non_root.py`, smoke `docker inspect` check).
- [ ] SR-041 AC 1, AC 6: running processes non-root on a started stack (`infra/smoke-test.sh`).
- [ ] The SPA is served through the proxy (smoke).

## Verification

```sh
cd infra && python3 -m pytest tests/test_images_non_root.py -v
docker compose -f infra/docker-compose.yml build frontend backend && docker compose -f infra/docker-compose.yml up -d && infra/smoke-test.sh
cd frontend && npm test
```

## Records

- **TS-015**: TC-015.1 (UID on images and running processes).
- **SOUP-024** (nginx): record that MedHub relies on the image running unprivileged on 8080; `in_review`.
- **ADD-026** 1.0: confirm `U-DEP-RuntimeUsers`.

## Definition of Done

- [ ] Infra tests and smoke pass on a started stack.
- [ ] TS-015 and SOUP-024 `in_review`.
- [ ] `traceability-check` shows no error for TASK-198, TS-015, SR-041.
