---
id: "PRB-041"
type: problem-report
title: "Gunicorn control server fails on every start because the service user has no home"
status: resolved
version: "1.5"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-11-13"
criticality: minor
links: []
tags: ["operations", "logging", "soup"]
---

# PRB-041 — Gunicorn control server fails on every start

## Observed

On every backend start the log shows
`[ERROR] Control server error: [Errno 13] Permission denied: '/home/medhub'`. The API workers start
and serve normally (login through the proxy returns 401).

## Investigation

- `backend/Dockerfile:18` creates the service user with `useradd -r` and no `-m`, so its `HOME`,
  `/home/medhub`, does not exist and `/home` is `root:root 755`.
- Gunicorn 26.0.0 (SOUP-005) enables its control socket by default (since 25.1.0). With
  `XDG_RUNTIME_DIR` unset it tries to create `$HOME/.gunicorn/gunicorn.ctl`; the control-server
  thread dies with `Errno 13` (`gunicorn/ctl/server.py:184` in the image).
- Effect: the `gunicornc` management interface (worker status, graceful reload) is unavailable.
  Nothing in the repository uses it. Reload (`HUP`) and shutdown (`TERM`) by signal do not depend
  on it: `--no-control-socket` only skips starting the control server.
- **Re-checked on 2026-11-12 (CR-005, Specify stage).** The mechanism is unchanged: Gunicorn is
  still 26.0.0 (`backend/uv.lock:706-707`), the user is still created without a home
  (`backend/Dockerfile:18`), and Compose sets neither `init` nor a `command:` for `backend`. The
  error was not re-observed in this stage because no stack was started.
- **The fix location moved.** Since CR-004 (TASK-191) `backend/entrypoint.sh` only runs
  `exec "$@"`. The Gunicorn command line is the image `CMD` at `backend/Dockerfile:24`, so the
  proposed edit to `entrypoint.sh` no longer applies. `celery-worker` and `celery-beat` run
  Celery, not Gunicorn (PRB-061), and are not affected.
- `--no-control-socket` exists in 26.0.0 (`gunicorn/config.py:3192-3194`, setting
  `control_socket_disable`, in the locked package).
- SOUP-005 already records that the control socket is on by default (anomaly review, its Findings
  table). It also notes a PID-1 reaping bug, #3220, fixed in 26.1.0, under which `init: true` could
  be considered. SOUP-005 judged that bug availability-only, with no trigger in MedHub.

## Impact

- No functional impact on the API.
- An ERROR line on every normal start trains operators to ignore backend log errors, which the
  monitoring behind RISK-007 relies on.
- An unused management interface is enabled by default.

## Safety evaluation

No effect on data integrity, a safety-related function or a clinical decision. No `release` record
exists, so no released version is affected and no notification is needed. Hence `minor`.

## Proposed resolution

Disable the unused control socket by adding `--no-control-socket` to the `gunicorn` command in
`backend/entrypoint.sh` (preferred), or create the user's home with `useradd -m`. Record in SOUP-005
that the control socket is on by default. Needs a task and a CR.

## Resolution

Fixed by CR-005 in TASK-214, which QA approved on 2026-11-13 (round 2). TASK-214 is the next
commit on branch `bug/build-hygiene`. The PRB is `resolved` and becomes `closed` once a release
ships the change.

- **Change.** `backend/Dockerfile` `CMD` gains `--no-control-socket` (Gunicorn 26.0.0 setting
  `control_socket_disable`). The second proposed route (`useradd -m`) was not taken: the user
  stays without a home. The edit is in the `CMD`, not `entrypoint.sh` (see Investigation).
  `infra/tests/test_backend_gunicorn_command.py` checks the flag in the final `CMD`, that Compose
  sets no `command:` for `backend`, and that `--forwarded-allow-ips=` appears exactly once and empty; it fails with the
  flag removed.
- **Before (build of `ff366ef`, started stack).** The backend log held
  `[ERROR] Control server error: [Errno 13] Permission denied: '/home/medhub'` once, right after
  `Booting worker`; `grep -cE 'Control server error|\[ERROR\]'` = 1.
- **After (started stack).** The same start-up through a login request answered 401 through the
  reverse proxy: no `Control server error` and no `[ERROR]` line (count 0). Log excerpts and the exact command form
  (scratch Compose copy, `--project-directory infra --env-file`, login on port 18443) are in
  TASK-214.
- **Records.** SOUP-005 1.3 (control socket disabled by configuration; version unchanged, no new
  anomaly review) and ADD-026 1.5 (flag named in `U-DEP-RuntimeUsers`).

## Source

Observed by the software developer during TASK-160 verification and confirmed by QA (2026-10-22).
Predates CR-001, which did not change the Gunicorn version; outside CR-001's scope.

## Version history

- 1.1 (2026-11-12) — Investigation re-checked for CR-005 (Specify stage): the mechanism is unchanged; the Gunicorn command now lives in the `backend/Dockerfile` `CMD`, not `entrypoint.sh`; the flag exists in 26.0.0; SOUP-005 already records the default. Criticality unchanged.
- 1.2 (2026-11-12) — `## Resolution` written for TASK-214 (CR-005). Status stays `open`; QA moves it.
- 1.3 (2026-11-13) — TASK-214 round 2: signal reload/shutdown unaffected noted; test description updated. Status stays `open`; at `resolved` QA rewords the "stays `open` until QA approves" sentence.
- 1.4 (2026-11-13) — QA approved TASK-214 (round 2): `open → resolved`; the Resolution's status sentence reworded. CR-005 `resolves` PRB-041.
- 1.5 (2026-11-13) — TASK-216 (TASK-214 QA round 2, LOW 3): the Investigation names `--no-control-socket` where it first said "the flag". Status unchanged.
