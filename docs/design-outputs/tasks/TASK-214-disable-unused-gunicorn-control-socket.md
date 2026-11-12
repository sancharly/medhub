---
id: "TASK-214"
type: task
title: "Disable the unused Gunicorn control socket"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-12"
updated: "2026-11-12"
links:
  - target: "SR-041"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-005"
    relation: relates_to
  - target: "PRB-041"
    relation: relates_to
  - target: "ADD-026"
    relation: relates_to
  - target: "SOUP-005"
    relation: relates_to
  - target: "TASK-210"
    relation: relates_to
tags: ["deployment", "logging", "soup", "cr:CR-005", "control:protective"]
---

# TASK-214 — Disable the unused Gunicorn control socket

- **Software item / unit:** SI-DEPLOY, backend image (`backend/Dockerfile` `CMD`, ADD-026).
  SOUP-005 Gunicorn 26.0.0.
- **PRB:** PRB-041. **CR:** CR-005 (AC-8; negative control).
- **Depends on:** TASK-210 (same Dockerfile).
- **Branch:** `bug/build-hygiene`.
- **Size:** S (`backend/Dockerfile`, new `infra/tests/test_backend_gunicorn_command.py`,
  SOUP-005, ADD-026, PRB-041).
- **Needs:** a Docker host for the started-stack check.
- **Trace note:** no SR states that the backend log is free of errors at start-up (CR-005
  Requirements decision). The task links `implements` SR-041 as the requirement of the
  deployment item it changes (ADD-026), as TASK-208 did; no SR-041 criterion changes (CR-005 Q-7).

## Objective

The backend no longer opens the unused `gunicornc` management interface, and its start-up log has
no ERROR line, so an ERROR in the backend log again means something (RISK-007 log monitoring).

## Implementation detail

1. `backend/Dockerfile` `CMD`: add `"--no-control-socket"` (Gunicorn 26.0.0 setting
   `control_socket_disable`, CR-005 A-4). Extend the comment above `CMD` by one line: the control
   socket is off because nothing uses it and the service user has no home (PRB-041).
2. Nothing else: the user stays without a home (`useradd -r`), no `init: true` (CR-005 Q-3), no
   Compose `command:` for `backend`.

## Tests (write first)

`infra/tests/test_backend_gunicorn_command.py` (standard library, as `test_images_non_root.py`):
- the final `CMD` of `backend/Dockerfile` is a JSON array that starts with `gunicorn` and contains
  `--no-control-socket`;
- the Compose `backend` service has no `command:` (so the image `CMD` is what runs);
- the existing `--forwarded-allow-ips=` stays (ADR-0019).

## Acceptance criteria

- [ ] CR-005 AC-8 (configuration): the CMD has `--no-control-socket`; the infra test passes, and
      fails with the flag removed (negative control).
- [ ] CR-005 AC-8 (started stack): from start-up through the first served request the backend log
      has no `Control server error` and no Gunicorn `[ERROR]` line, and a login through the reverse
      proxy is answered (401 for a wrong password). Log excerpt recorded here.
- [ ] Records: SOUP-005 states the control socket is disabled by configuration (relied-on
      configuration, Findings row, change log; version unchanged, so no new anomaly review);
      ADD-026 names the flag in the backend unit; PRB-041 `## Resolution` written.

## Verification

```sh
python3 -m unittest discover -s infra/tests -v
docker build -t medhub-backend:ci ./backend
docker image inspect medhub-backend:ci --format '{{json .Config.Cmd}}'
# scratch project with a generated infra/.env (as in TASK-208), then:
docker compose -p task214 -f infra/docker-compose.yml up -d --build --wait
curl -sk -o /dev/null -w '%{http_code}\n' -X POST https://localhost/api/v1/auth/login \
  -H 'Content-Type: application/json' -d '{"email":"nobody@test.invalid","password":"x"}'
docker compose -p task214 -f infra/docker-compose.yml logs --no-color backend | grep -cE 'Control server error|\[ERROR\]'   # 0
docker compose -p task214 -f infra/docker-compose.yml down -v
```

The login path and the generated `.env` follow `infra/smoke-test.sh` and `infra/DEPLOY.md`; the
developer's own `infra/.env` and volumes are not touched.

## Records

- **SOUP-005** (`approved` 1.2) → 1.3, `in_review`, approval record cleared.
- **ADD-026** (`approved` 1.4) → 1.5, `in_review`, approval record cleared.
- **PRB-041**: `resolved` only after QA approves (AC-11).

## Version history

- 1.0 (2026-11-12) — Created at the CR-005 Plan stage (Software Architect role); `draft`.
