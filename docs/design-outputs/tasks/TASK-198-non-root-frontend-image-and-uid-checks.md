---
id: "TASK-198"
type: task
title: "Run the frontend image as a non-root user and check every built image's UID"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-11-01"
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

- [x] SR-041 AC 1: image configuration non-root for every built image
      (`infra/tests/test_images_non_root.py`, smoke `docker inspect` check).
- [x] SR-041 AC 1, AC 6: running processes non-root on a started stack (`infra/smoke-test.sh`).
- [x] The SPA is served through the proxy (smoke).

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

- [x] Infra tests and smoke pass on a started stack.
- [x] TS-015 and SOUP-024 `in_review`.
- [x] `traceability-check` shows no error for TASK-198, TS-015, SR-041.

## Implementation notes (software developer, 2026-11-01)

- `frontend/Dockerfile`: the runtime stage keeps the pinned `nginx` image and adds one `RUN` (delete the
  `user` directive, `pid /tmp/nginx.pid`, `chown -R nginx:nginx /var/cache/nginx`) and `USER nginx`.
  The official image's temp paths live in `/var/cache/nginx` and its log files are symlinks to
  stdout/stderr, so nothing else needed to move. `frontend/nginx.conf`: `listen 8080`.
  `infra/reverse-proxy/nginx.conf`: `proxy_pass http://frontend:8080`. `infra/docker-compose.yml`:
  `frontend` `expose: "8080"`.
- `infra/tests/test_images_non_root.py` (7 tests): Dockerfile final `USER` of every service with
  `build:` (discovered from Compose, so a new built image is covered), no root `user:` override,
  frontend port, proxy target and `expose:`, pid/cache paths.
- `infra/smoke-test.sh` section 11 (new): for each Compose service with `build:` it checks the image's
  `Config.User` (from the container's image, also for the exited one-shot services), PID 1 UID from
  `/proc/1/status` and `id -u` for running ones, and `https://localhost/` returns 200 with the app
  root. Skipped only when no container of the project exists. Carried item done: the config-only
  copy of `.env.example` now fills the five secret settings with throwaway values (checked: the
  filled copy renders with `docker compose config`; the bare template is refused).
- Deviation: the task says `docker compose exec <svc> id -u`; the smoke test checks that and PID 1's
  UID, because `exec` reports the exec user, not necessarily the main process.
- PRB-061: the `celery-worker` container runs gunicorn, not Celery, so its UID check covers gunicorn
  until TASK-191 fixes it; repeat the check there.
- Not changed: ADD-026 (already states `U-DEP-RuntimeUsers` and 8080; no edit needed), the pulled
  images (reverse proxy, PostgreSQL, Redis, SeaweedFS), which are outside SR-041 AC 1. The reverse
  proxy still runs its master as root (image default, port 80/443), as ADD-026 allows.
- Records: TS-015 1.2 (`in_review`, TC-015.1), SOUP-024 1.3 (`in_review`, approval cleared, reliance on
  the unprivileged image on 8080), PRB-007 1.5 (interim note, still `open`).

### AC to test

| AC | Test |
|---|---|
| SR-041 AC 1, image configuration | `test_backend_image_ends_as_an_unprivileged_user`, `test_frontend_image_ends_as_an_unprivileged_user`, `test_every_built_compose_image_is_covered_and_non_root`, `test_compose_does_not_override_a_built_image_to_root`; smoke `Config.User` checks |
| SR-041 AC 1, AC 6 running processes | smoke `PID 1 UID` and `id -u` checks on `backend`, `celery-worker`, `frontend` |
| SPA through the proxy | smoke "the SPA index is served through the reverse proxy (200)"; `test_proxy_targets_the_frontend_port`, `test_frontend_listens_on_an_unprivileged_port` |

### Started-stack evidence (project `task198`, temporary env file, `down -v` afterwards)

- `Config.User`: backend `medhub`, celery-worker `medhub`, frontend `nginx`, object-store-init `medhub`, object-store-preflight `medhub`.
- Frontend `ps`: master (PID 1) and four workers as `nginx`; `uid=101(nginx)`; listening on `0.0.0.0:8080` only. Backend `uid=999(medhub)`.
- `https://localhost/` and `https://localhost/some/spa/route` through the proxy: 200 `text/html`.
- `infra/smoke-test.sh`: 38 passed, 0 failed (12 in section 11).
- Negative controls: `USER nginx` removed: unit tests 2 failures, rebuilt stack smoke 3 FAIL (`Config.User` empty, PID 1 UID 0, `id -u` 0), 35 passed; proxy at `frontend:80`: `test_proxy_targets_the_frontend_port` fails. Files restored.

### Verification run

| Command | Result |
|---|---|
| `cd infra && python3 -m unittest discover -s tests` | 55 OK (7 new) |
| `cd frontend && npm test -- --run`; `npm run build` | 155 passed (27 files); build OK |
| `uv run pytest --cov=app --cov-fail-under=85` | 1056 passed, 4 skipped; 94.13 % |
| `ruff check .`, `black --check .`, `mypy app` | clean; 246 files unchanged; no issues in 128 files |
| `infra/.env` checksum before and after | unchanged (`714c7630...`) |

## QA review round 1 (QA engineer, 2026-11-01): APPROVED

TASK-198 `in_review → approved`; TS-015 1.2 `in_review → approved`. SOUP-024 1.3 stays
`in_review`: the human approves it. No CRITICAL or HIGH finding.

- **nginx unprivileged.** I built the image myself. `Config.User` is `nginx`. `nginx -T` shows no
  `user` directive in any included file (`nginx.conf`, `mime.types`, `conf.d/default.conf`) and
  shows `pid /tmp/nginx.pid`. The compiled temp paths (client_body, proxy, fastcgi, uwsgi, scgi)
  are all under `/var/cache/nginx`, which is owned by `nginx:nginx`. The logs are symlinks to
  stdout/stderr. `nginx -t` passes as uid 101. I also ran the image `--read-only` with tmpfs
  `/tmp` and `/var/cache/nginx`, `--cap-drop ALL` and `no-new-privileges`: the master (PID 1) and
  the four workers ran as `nginx` (`Uid: 101`), it listened on `0.0.0.0:8080` only, and both `/`
  and `/some/spa/route` returned 200 `text/html`.
- **Port 80.** No other reference to the frontend on port 80 remains: no healthcheck, CI job,
  Vite config, `infra/DEPLOY.md` or arc42 07 entry. `DEPLOY.md` does not mention the frontend
  port. The only port 80 left is the reverse proxy's published `80:80`, which is correct.
- **Pulled images.** SR-041 AC 1 says "every container image MedHub builds". On the started stack,
  postgres (PID 1 UID 999), redis (999) and SeaweedFS (1000) drop privileges themselves. The
  reverse proxy's master runs as UID 0, with workers as `nginx`. That is outside AC 1, as
  ADD-026 says, so there is no AC violation. See finding 1.
- **PRB-061.** The caveat is stated in the smoke-test comment, in the TASK-198 notes, in TS-015 and in
  PRB-007. It is not written in TASK-191. See finding 3.
- **Config-only path.** In a scratch copy of the tree with no `infra/.env`, `docker compose
  config` renders, the file is removed on exit, and section 11 prints SKIP. The values are not
  placeholders (`is_placeholder` is False for all five). If a stack were started with them,
  `secret_settings.check` would refuse `DATABASE_URL` (not a URL) and `AT_REST_ENCRYPTION_KEY`
  (24 bytes), so the backend would not start on that file.

### Findings

1. **MEDIUM — PRB-007 does not record the root reverse-proxy master.**
   `docs/problem-reports/PRB-007-container-runs-as-root-insecure-defaults.md:93-98` says "Item 1
   is fixed". The title is "Runtime container runs as root", and the internet-facing
   `reverse-proxy` (pulled `nginx` image) still runs its master as UID 0. The release
   residual-anomaly evaluation reads PRB-007, so the residual should be visible there.
   → Add one sentence to the interim note or Investigation: the reverse proxy master runs as root
   (image default, ports 80/443), postgres, redis and SeaweedFS drop to UIDs 999, 999 and 1000,
   and all four are outside SR-041 AC 1 (ADD-026). Leave the decision to keep it to the human.
   PRB-007 stays `open` (TASK-196 and TASK-191), so this can go in with its next edit. Carried.
2. **LOW — section 11 skips the running-process check without saying so.**
   `infra/smoke-test.sh:263` checks PID 1 and `id -u` only when the container is running. For
   a long-running service that has stopped, nothing is printed. My probe: with `celery-worker`
   stopped, section 11 showed only its `Config.User` PASS. The overall result was not green
   (section 10's probe FAILed), so this did not give a false pass.
   → For services whose restart policy is not `"no"`, report a FAIL ("not running") when the
   container is not running. Carried.
3. **LOW — the PRB-061 re-check is not carried in TASK-191.**
   `docs/design-outputs/tasks/TASK-191-*.md` runs the whole smoke test (`:111`), so section 11
   runs again, but no acceptance item asks for UID evidence on the real Celery worker and beat.
   → When TASK-191 starts, add an acceptance item: section 11 PASS for `celery-worker` and the
   beat service, with `ps` showing the Celery process under a UID other than 0. Carried.
4. **LOW — short-form `build:` is not discovered.** `infra/tests/test_images_non_root.py:38`
   (`built_dockerfiles`) matches only the long form (`build:` with `context:` and `dockerfile:`).
   A new service written as `build: ./dir` is not checked. The smoke test's `compose config`
   discovery does cover it.
   → Accept the short form too, or assert that every block containing `build:` was parsed.
5. **LOW — the image still advertises port 80.** `Config.ExposedPorts` is `80/tcp`, inherited
   from the base image. → Add `EXPOSE 8080` to `frontend/Dockerfile` for documentation. The
   inherited 80 cannot be removed.
6. **LOW — TS-015 lists AC 1 twice.**
   `docs/design-outputs/tests-specifications/TS-015-deployment-secrets-and-non-root-containers.md:45`
   says "AC 1 maps to TC-015.1 … AC 1 and AC 6 map to TC-015.1". → Drop the first mention at
   the next edit.

### Verification run (QA)

| Command | Result |
|---|---|
| `docker build -t qa198-frontend:test frontend`; `docker inspect` | `Config.User=nginx`; ExposedPorts `80/tcp` (inherited) |
| `docker run --entrypoint sh … -c 'id; nginx -t; nginx -T; nginx -V'` | uid 101; syntax ok; no `user`; `pid /tmp/nginx.pid`; temp paths under `/var/cache/nginx` (owned by `nginx`) |
| `docker run --read-only --tmpfs /tmp --tmpfs /var/cache/nginx:uid=101 --cap-drop ALL --security-opt no-new-privileges` | running; PID 1 and workers as `nginx`; `0.0.0.0:8080` only; 200 on `/` and `/some/spa/route` |
| Started stack, project `qa198`, scratch env file (fresh generated secrets), `up -d --build` | 9 containers; backend healthy |
| `infra/smoke-test.sh` (`COMPOSE_PROJECT_NAME=qa198`, run from a scratch copy of the tree whose `.env` is the scratch file; the developer's `infra/.env` does not render) | 38 passed, 0 failed (11 PASS in section 11, plus the SPA check) |
| Negative control (started stack): `USER nginx` removed, frontend rebuilt | 35 passed, 3 failed (`Config.User ''`, PID 1 UID 0, `id -u` 0); restored: 38/0 |
| Unit mutations on a scratch copy: no `USER`; `USER root` appended; Compose `user: "0:0"`; `listen 80`; `pid /run/nginx.pid` | 2, 2, 1, 1 and 1 failures; baseline 7 OK |
| `down -v` | 0 containers, volumes or networks left for `qa198`; `infra/.env` checksum unchanged |
| `python3 -m unittest discover -s infra/tests` | 55 OK |
| `npm test -- --run`; `npm run build`; `lint`; `typecheck` | 155 passed (27 files); build OK; clean |
| `uv run pytest --cov=app --cov-fail-under=85` | 1056 passed, 4 skipped; 94.13 % |
| `ruff check .`, `black --check .`, `mypy app`; `python3 infra/check_image_pins.py` | clean; 246 unchanged; no issues in 128 files; pins rc 0 |
| traceability (TASK-198, TS-015, SOUP-024, PRB-007, SR-041) | 0 errors, 13 warnings after this approval: W5 for approved records linking `in_review` SOUP-024/004/005 and ADD-026 (new: ADD-018, ADD-005, RISK-005, RISK-010 → SOUP-024 until the human re-approves it, and TASK-198 → ADD-026, like TASK-197 and TASK-203), and 2 W6 on CR-002 (pre-existing) |
