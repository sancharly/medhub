---
id: "TASK-214"
type: task
title: "Disable the unused Gunicorn control socket"
status: approved
version: "1.4"
author: "Carlos Santiago Liceras"
created: "2026-11-12"
updated: "2026-11-13"
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

- [x] CR-005 AC-8 (configuration): the CMD has `--no-control-socket`; the infra test passes, and
      fails with the flag removed (negative control).
- [x] CR-005 AC-8 (started stack): from start-up through the first served request the backend log
      has no `Control server error` and no Gunicorn `[ERROR]` line, and a login through the reverse
      proxy is answered (401 for a wrong password). Log excerpt recorded here.
- [x] Records: SOUP-005 states the control socket is disabled by configuration (relied-on
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

## Verification results (Software Developer, 2026-11-12)

Files changed: `backend/Dockerfile` (`CMD` + comment), new `infra/tests/test_backend_gunicorn_command.py`
(3 tests), `infra/tests/test_compose_db_roles.py:82` (see below), `docs/soup/SOUP-005-gunicorn.md` (1.3),
`docs/design-outputs/architecture/ADD-026-deployment-configuration-and-runtime-hardening.md` (1.5),
`docs/problem-reports/PRB-041-gunicorn-control-socket-permission-error.md` (`## Resolution`, 1.2).
`SOUP-005` and `ADD-026` are `in_review` with the approval record cleared; PRB-041 stays `open`.

**Existing test adjusted.** `test_compose_db_roles.StaticWiring.test_gunicorn_is_the_image_default_command`
matched the `CMD` ending exactly `"--forwarded-allow-ips=", "app.main:app"]`; the new flag sits between
them, so the regex gained `.*` before `"app.main:app"`. Nothing else in it changed.

- Test first: the new test failed on `--no-control-socket` before the edit (1 failure of 3).
- Negative control: with `"--no-control-socket",` removed from the `CMD`, `python3 -m unittest discover -s infra/tests -p 'test_backend_gunicorn*'` gave `FAILED (failures=1)` (`'--no-control-socket' not found in ['gunicorn', '-k', ...]`); restored, `OK`.
- `python3 -m unittest discover -s infra/tests`: `Ran 163 tests ... OK`. `python3 infra/check_image_pins.py`: exit 0.
- `docker build -t medhub-backend:ci ./backend`; `docker image inspect ... .Config.Cmd` =
  `["gunicorn","-k","uvicorn.workers.UvicornWorker","-b","0.0.0.0:8000","--forwarded-allow-ips=","--no-control-socket","app.main:app"]`.

**Started stack.** Project `task214`, generated scratch `.env` (random secrets, outside the repo, not
committed), Compose file copied to the scratchpad with only the host ports (18080/18443) and the
`medhub` subnet (10.78.78.0/24, proxy 10.78.78.2, `TRUSTED_PROXIES`) changed, because the developer's
own stack was running on 80/443 and 10.77.77.0/24; `--project-directory infra`, so build contexts,
the proxy config and certificates are the repository's. Torn down with `down -v --rmi local`; no
`task214` container or volume remains; the developer's stack was not touched.

Before (build of `ff366ef`; login through the proxy `HTTP 401`; `grep -cE 'Control server error|\[ERROR\]'` = 1):

```
[1] [INFO] Starting gunicorn 26.0.0
[1] [INFO] Listening at: http://0.0.0.0:8000 (1)
[1] [INFO] Using worker: uvicorn.workers.UvicornWorker
[7] [INFO] Booting worker with pid: 7
[1] [ERROR] Control server error: [Errno 13] Permission denied: '/home/medhub'
[7] [INFO] Started server process [7]
[7] [INFO] Waiting for application startup.
MedHub API starting up ... [7] [INFO] Application startup complete.
```

After (this change; login through the proxy `HTTP 401`; same grep = 0):

```
[1] [INFO] Starting gunicorn 26.0.0
[1] [INFO] Listening at: http://0.0.0.0:8000 (1)
[1] [INFO] Using worker: uvicorn.workers.UvicornWorker
[7] [INFO] Booting worker with pid: 7
[7] [INFO] Started server process [7]
[7] [INFO] Waiting for application startup.
MedHub API starting up ... [7] [INFO] Application startup complete.
```

Login request: `curl -sk -X POST https://localhost:18443/api/v1/auth/login` with an unknown e-mail and a wrong password.

Exact command form used (the `## Verification` block above shows the intended recipe; the run
differed because the developer's stack held 80/443 and 10.77.77.0/24). `<scratch>` is a directory
outside the repository holding `docker-compose.yml` (a copy of `infra/docker-compose.yml` with only
host ports 18080/18443 and the `medhub` subnet 10.78.78.0/24, proxy 10.78.78.2 and
`TRUSTED_PROXIES` changed) and a generated `.env`:

```sh
docker compose -p task214 -f <scratch>/docker-compose.yml --project-directory infra \
  --env-file <scratch>/.env up -d --build --wait
curl -sk -o /dev/null -w '%{http_code}\n' -X POST https://localhost:18443/api/v1/auth/login \
  -H 'Content-Type: application/json' -d '{"email":"nobody@test.invalid","password":"x"}'   # 401
docker compose -p task214 -f <scratch>/docker-compose.yml --project-directory infra \
  --env-file <scratch>/.env logs --no-color backend | grep -cE 'Control server error|\[ERROR\]'
docker compose -p task214 -f <scratch>/docker-compose.yml --project-directory infra \
  --env-file <scratch>/.env down -v --rmi local
```

Not changed (outside this task): SOUP-005 still says "`backend/entrypoint.sh`" for the Gunicorn command
in two body paragraphs ("MedHub use and judgement", "Forwarded-header handling"); since TASK-191 that
is the image `CMD`. Left for a record revision.

## QA review round 1 (2026-11-12): CHANGES REQUESTED

No CRITICAL or HIGH finding. The change itself is correct and AC-8 is met on a started stack. Two
MEDIUM findings have to be fixed in this task: SOUP-005 is already at revision 1.3 here, and the
test edit removed a check that the suite had at HEAD. The LOW findings are fixed in the same round.

- **[MEDIUM] SOUP-005 1.3 body still describes the pre-TASK-191 command and an open PRB-041.**
  `docs/soup/SOUP-005-gunicorn.md:67` ("Gunicorn only supervises the Uvicorn workers
  (`backend/entrypoint.sh`)") and `:79` ("`backend/entrypoint.sh` starts Gunicorn with
  `--forwarded-allow-ips=`"): since TASK-191, `entrypoint.sh` only runs `exec "$@"`. The command,
  including the relied-on `forwarded_allow_ips` setting (SR-042), is the `CMD` at
  `backend/Dockerfile:26`. `:68` still says "The control-socket failure is PRB-041 (open, minor)",
  and `:72-73` say "When PRB-041 is fixed, its CR can also consider `init: true`". CR-005 Q-3
  already decided against `init`. → In the same 1.3 revision, change both `entrypoint.sh`
  references to "the backend image `CMD` (`backend/Dockerfile`)". Reword the PRB-041 sentences to
  say the control socket is disabled by configuration since TASK-214 and that `init: true` was
  considered and not adopted (CR-005 Q-3). Mention both edits in the 2026-11-12 change-log line.
- **[MEDIUM] Loosened regex: the suite no longer detects a later override of the empty
  `--forwarded-allow-ips` (SR-042, ADR-0019).** `infra/tests/test_compose_db_roles.py:82`. At HEAD
  the regex needed `"--forwarded-allow-ips="` to come immediately before `"app.main:app"`, so it was
  the last forwarded flag on the command line. Gunicorn's parser keeps the last value: with
  `--forwarded-allow-ips= --forwarded-allow-ips=*` the setting is `'*'` (checked with the locked
  26.0.0 `Config().parser()`). With the added `.*`, the mutant
  `"--forwarded-allow-ips=", "--forwarded-allow-ips=*", "--no-control-socket", "app.main:app"`
  passes the **whole** infra suite: 163 OK in a scratch git copy. The HEAD regex rejected the
  same override. `test_compose_trusted_proxy.py:90` and the new
  `test_cmd_keeps_the_empty_forwarded_allow_ips` (`assertIn`) both check only that the flag is
  present. → In `infra/tests/test_backend_gunicorn_command.py`, make
  `test_cmd_keeps_the_empty_forwarded_allow_ips` assert
  `[a for a in cmd if a.startswith("--forwarded-allow-ips")] == ["--forwarded-allow-ips="]`, so
  the flag appears exactly once and is empty. Add that mutant to the negative-control evidence.
  The `.*` in `test_compose_db_roles.py:82` can then stay; that test is meant to pin "gunicorn is
  the image default command, `app.main:app` last" (TASK-191).
- **[LOW] "graceful reload" wording suggests a capability was lost.** SOUP-005 relied-on
  configuration paragraph (`:27-29`) and PRB-041 Investigation say `gunicornc` provides worker
  status and graceful reload. Signal handling does not depend on the control socket
  (`gunicorn/arbiter.py:953-977`: the flag only skips `_start_control_server`). On the started
  stack, `SIGHUP` re-spawned the worker and later logins were answered 401, and `SIGTERM`
  (`compose stop`) shut down cleanly with exit 0. The log had no `[ERROR]`. → Add one sentence to
  SOUP-005: graceful reload (`HUP`) and shutdown (`TERM`) by signal are unaffected; only the
  socket interface is off.
- **[LOW] PRB-041 Resolution: a sentence goes stale on the status change, and the command recipe
  is not in the record.** `docs/problem-reports/PRB-041-gunicorn-control-socket-permission-error.md`
  `## Resolution` says "the PRB stays `open` until QA approves". The TASK's `## Verification`
  block uses `-f infra/docker-compose.yml` and `https://localhost`. The run actually used a scratch
  Compose copy on 18443 with `--project-directory infra` and `--env-file`. → Add the exact
  `docker compose -p … -f <scratch copy> --project-directory infra --env-file <scratch .env>`
  form and the 18443 login URL to the evidence. When QA moves the PRB to `resolved`, change the
  stay-open sentence to say so.

**QA verification run (2026-11-12, working tree on `ff366ef`):**
- `python3 -m unittest discover -s infra/tests`: 163 tests, OK. `python3 infra/check_image_pins.py`: exit 0.
- `backend/uv.lock:706-707` locks gunicorn 26.0.0. `backend/.venv/.../gunicorn/config.py:3191-3197`
  defines `ControlSocketDisable` with `cli = ["--no-control-socket"]`, `store_true`, default False.
  `arbiter.py:960` returns before the control server is created.
- Negative controls, in a scratch git copy, against the full suite: flag removed → 1 failure
  (`test_cmd_starts_gunicorn_without_the_control_socket`); `command:` added to the Compose
  `backend` → 1 failure (`test_compose_does_not_replace_the_backend_cmd`); later
  `--forwarded-allow-ips=*` → **OK** (MEDIUM above).
- Started stack, a separate project `qa214`: the developer's scratch Compose copy, which differs
  from `infra/docker-compose.yml` only in host ports 18080/18443 and subnet 10.78.78.0/24;
  `--project-directory infra`; a freshly generated `.env` (deleted afterwards). Volumes resolved
  to `qa214_*`. `up -d --build --wait` exit 0. The image and container `Config.Cmd` were
  `["gunicorn","-k","uvicorn.workers.UvicornWorker","-b","0.0.0.0:8000","--forwarded-allow-ips=","--no-control-socket","app.main:app"]`,
  and `docker top` showed the same argv for master and worker. The login through the proxy
  (`POST https://localhost:18443/api/v1/auth/login`, unknown e-mail) returned 401 problem+json.
  The backend log from `Starting gunicorn 26.0.0` through `Application startup complete` had
  `grep -cE 'Control server error|\[ERROR\]'` = 0. PID 1 had 1 thread and there was no
  `gunicorn.ctl`. After `SIGHUP` the count stayed 0; `stop` gave exit 0. Then
  `down -v --rmi local`: no `qa214` container, volume or network remained. The user's `infra`
  stack and its `infra_*` volumes were not touched (up 2 days, healthy).
- Worker/master behaviour (RISK-007, SRs): no SR, RISK, script or runbook uses `gunicornc`
  (repository grep). Before this change the control-server thread already died at start-up, so
  the running behaviour is unchanged apart from the removed ERROR line.
- `traceability-check` (two-hop CR-005 scope, 171 records): **0 errors**, 24 W5 and 7 W6. The new
  W5s are approved records linking ADD-026 and SOUP-005, which are back in `in_review`; the other
  warnings are known and pre-existing.

## Round 2 (Software Developer, 2026-11-13): response to QA round 1

No code other than the test changed; no stack restart.

| Finding | Fix |
|---|---|
| MEDIUM SOUP-005 stale text | `docs/soup/SOUP-005-gunicorn.md` (still 1.3, `in_review`): both `backend/entrypoint.sh` references now say the backend image `CMD` (`backend/Dockerfile`); PRB-041 is described as disabled by configuration since TASK-214, not open; the `init: true` sentence now says it was considered and not adopted (CR-005 Q-3). The existing 2026-11-12 change-log line names all three corrections; `updated` is 2026-11-13. |
| MEDIUM override of the empty flag | `test_cmd_keeps_the_empty_forwarded_allow_ips` now asserts `[a for a in cmd if a.startswith("--forwarded-allow-ips")] == ["--forwarded-allow-ips="]`. `.*` in `test_compose_db_roles.py:82` kept. |
| LOW "graceful reload" wording | SOUP-005 relied-on configuration and PRB-041 Investigation each gain one sentence: reload (`HUP`) and shutdown (`TERM`) by signal are unaffected; the flag only skips starting the control server. |
| LOW command form / PRB wording | Exact scratch-copy command form recorded above (ports 18080/18443, subnet 10.78.78.0/24, `--project-directory infra --env-file <scratch>/.env`). PRB-041 stays `open` (1.3); its Resolution sentence "stays `open` until QA approves TASK-214, then `resolved`" is left for QA to reword at `resolved`. |

Negative control for the override mutant (scratch `git clone` of the repository plus the working-tree
changes; baseline 163 tests OK). `CMD` mutated to
`"--forwarded-allow-ips=", "--forwarded-allow-ips=*", "--no-control-socket", "app.main:app"`:
`python3 -m unittest discover -s infra/tests` gave `Ran 163 tests`, `FAILED (failures=1)`:
`test_cmd_keeps_the_empty_forwarded_allow_ips`, `Lists differ: ['--forwarded-allow-ips=',
'--forwarded-allow-ips=*'] != ['--forwarded-allow-ips=']`. (Round 1: the same mutant passed.)

Re-run in the working tree: `python3 -m unittest discover -s infra/tests` `Ran 163 tests ... OK`;
`python3 infra/check_image_pins.py` exit 0.

## QA review round 2 (2026-11-13): APPROVED

All four round-1 findings are fixed. No CRITICAL, HIGH or MEDIUM finding; the LOW findings below
do not block.

**Override mutants**, run in a scratch git copy of the working tree (baseline 163 tests OK), each
against the full `python3 -m unittest discover -s infra/tests`:

| `CMD` mutant (around `"--no-control-socket"`) | Gunicorn 26.0.0 value (locked `Config().parser()`) | Suite |
|---|---|---|
| `"--forwarded-allow-ips="`, `"--forwarded-allow-ips=*"` (after) | `'*'` | FAILED (1): `test_cmd_keeps_the_empty_forwarded_allow_ips` |
| `"--forwarded-allow-ips=*"`, `"--forwarded-allow-ips="` (before) | `''` (harmless, still rejected) | FAILED (1): same test |
| `"--forwarded-allow-ips="`, `"--forwarded-allow-ips"`, `"*"` (two argv items, after) | `'*'` | FAILED (1): same test |
| `"--forwarded-allow-ips"`, `"*"`, `"--forwarded-allow-ips="` (two argv items, before) | `''` | FAILED (1): same test |
| `--no-control-socket` removed | n/a | FAILED (1): `test_cmd_starts_gunicorn_without_the_control_socket` |
| `"--forwarded-allow-ips="`, `"--forwarded-allow=*"` (abbreviated option) | `'*'` | **OK** (LOW 1) |

The two-argv form matters: Gunicorn accepts it and it sets `'*'`. The `startswith` filter catches it
because the bare option name is itself a matching item. `GUNICORN_CMD_ARGS` and
`$FORWARDED_ALLOW_IPS` cannot override the flag: Gunicorn applies command-line settings last
(`gunicorn/app/base.py:189-192`), and Compose sets neither.

**Records.** SOUP-005 1.3: both `backend/entrypoint.sh` references now name the image `CMD` (`:68`,
`:80`; `entrypoint.sh` is `exec "$@"`). PRB-041 is described as disabled by configuration since
TASK-214 (`:59`, `:69`). `init: true` is recorded as considered and not adopted, per CR-005 Q-3
(`:73-74`, matching CR-005 `:157`, `:279`). The signal sentence is at `:28-29`. The 2026-11-12
change-log line names all four. PRB-041 Investigation and Resolution match the code. `useradd -r`
is at `Dockerfile:18`, the `Control server error` log call at `ctl/server.py:184`, and the HEAD
`CMD` at `:24`. The Resolution points to TASK-214 for the exact command form, which TASK-214 records
(scratch copy, `--project-directory infra --env-file`, 18443), so the run can be reproduced. The
`Dockerfile` (round-1 stack check still applies), ADD-026 and `test_compose_db_roles.py` have not
changed since round 1.

**LOW findings (not blocking; for TASK-216 or the next revision of the record):**
- **[LOW 1] Abbreviated option bypasses the forwarded-flag test.** `infra/tests/test_backend_gunicorn_command.py:38`.
  Gunicorn's parser has `allow_abbrev=True`, so `--forwarded-allow=*` (or a shorter prefix) after
  the empty flag sets `'*'`, and the whole suite stays OK. Nobody would write this by accident, so
  it is not blocking. → Match on the option name instead: take `a.split("=", 1)[0]` for each `--`
  argument and select it when `"--forwarded-allow-ips".startswith(name)` and the name is at least
  `--forwarded` long.
- **[LOW 2] Wording slips in SOUP-005.** `docs/soup/SOUP-005-gunicorn.md:80` starts a sentence in
  lower case ("the backend image `CMD` ..."). The change-log line dates QA round 1 as 2026-11-13;
  round 1 was 2026-11-12. → Capitalise "The" and change the date to 2026-11-12 at the next
  revision.
- **[LOW 3] PRB-041 Investigation `:31-32` refers to "the flag" before it is introduced (`:41`).**
  → Say "`--no-control-socket` only skips starting the control server".

**QA verification run (2026-11-13, working tree on `ff366ef`):**
- `python3 -m unittest discover -s infra/tests`: `Ran 163 tests ... OK`. `python3 infra/check_image_pins.py`: exit 0.
- Mutants: see the table above.
- `traceability-check` (two-hop CR-005 scope, 171 records): **0 errors**, 31 warnings (24 W5, 7 W6),
  the same set as round 1. These are the known approved-on-`in_review` links to SOUP-005, ADD-026 and
  the other CR-005 records, and the pre-existing W6 links to obsolete records. PRB-041 → `resolved`
  has its incoming `resolves` link from CR-005 (E9 satisfied).
  Re-run after the status changes: 0 errors, 33 warnings. The two new ones are W5 from TASK-214
  (`approved`) to ADD-026 and SOUP-005 (`in_review`); they clear when the human approves those records.

## Version history

- 1.0 (2026-11-12) — Created at the CR-005 Plan stage (Software Architect role); `draft`.
- 1.1 (2026-11-12) — Implemented; evidence added; `draft` → `in_review` (Software Developer role). QA approves.
- 1.2 (2026-11-12) — QA review round 1: CHANGES REQUESTED (2 MEDIUM, 2 LOW, above); `in_review → draft`.
  PRB-041 stays `open`.
- 1.3 (2026-11-13) — Round 2: the four QA findings fixed (above); `draft` → `in_review` (Software Developer role). QA approves.
- 1.4 (2026-11-13) — QA review round 2: APPROVED (3 LOW, non-blocking, above). `in_review → approved`;
  boxes ticked; PRB-041 `open → resolved`; SOUP-005 and ADD-026 stay `in_review` for the human.
