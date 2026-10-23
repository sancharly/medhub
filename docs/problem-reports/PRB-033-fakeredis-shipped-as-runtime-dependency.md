---
id: "PRB-033"
type: problem-report
title: "fakeredis is declared as a runtime dependency and ships in the production image"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-21"
updated: "2026-10-22"
criticality: minor
links: []
tags: ["soup", "configuration-management"]
---

# PRB-033 — fakeredis is declared as a runtime dependency

## Observed

`backend/pyproject.toml` lists `fakeredis>=2.36.2` under `[project] dependencies`, so it is
installed into the production image. No module under `backend/app/` or `backend/modules/` imports
it; only the test suite does.

## Impact

- An in-memory Redis imitation ships in the product without being relied on, adding an unreviewed
  SOUP item ([SOUP-018](../soup/SOUP-018-fakeredis.md)) and attack surface for no function.
- A misconfiguration that wires it in place of the real client would silently drop sessions on
  restart; nothing prevents that today.

## Investigation

Mechanism. `fakeredis>=2.36.2` was listed in `[project] dependencies` of `backend/pyproject.toml`
(line 21, as of commit `c455618`, before CR-001) instead of the `dev` dependency group (`:26-35`).
`backend/Dockerfile:7` installs with `uv sync --frozen --no-dev`, which installs every runtime
dependency of `backend/uv.lock`, so `fakeredis` 2.36.2 and its `sortedcontainers` dependency were
built into the production image. Nothing in the application needs it: no file under `backend/app/`
or `backend/modules/` references `fakeredis` or `FakeRedis` (grep, empty). Only the test suite
imports it, in six files: `backend/tests/auth/test_session_service.py:9`,
`backend/tests/auth/test_lockout.py:7`, `backend/tests/api/test_lockout_integration.py:13`,
`backend/tests/identity/test_erasure.py:9`, `backend/tests/identity/test_lifecycle.py:8` and
`backend/tests/workers/test_session_revoke.py:8`.

Root cause: the package was added to the runtime list with the phase-2 auth and session layer
(commit `845886c`, TASK-020..036) although only its tests use it, and no control compared what the product imports with what the production image installs. The
same gap allowed PRB-002 in the opposite direction (imported, not declared).

Reproduction on the unfixed tree: build the backend image and run
`docker run --rm --entrypoint python medhub-backend:ci -c "import fakeredis"`; it succeeds, and the
check `find_spec('fakeredis') is not None` of TC-013.8 exits 1.

## Safety evaluation

No hazard is realized: the package is unused at runtime. It would contribute to RISK-005 and
RISK-007 only through the misconfiguration described above. A FakeRedis wired in place of the real
client would hold sessions in one process per gunicorn worker: every session is lost on restart
(availability, RISK-007), and a session revoked on one worker stays valid on the others, which
defeats SR-030 revocation (RISK-005). No such wiring exists, and no control of either risk depends
on `fakeredis`. It affects no data integrity, safety-related function or clinical decision, so
`criticality: minor` stands.

Released versions (§9.3): no `release` record exists (`docs/releases/` is absent), so no released
version in use is affected and no notification is needed.

## Resolution

Resolved by CR-001 (`resolves` link on the CR) in TASK-158, on branch `bug/soup-pinning`. The
proposal was carried out as written: `fakeredis` moved to the `dev` dependency group, the lock
refreshed, SOUP-018 made `obsolete` in the same change. Verification is automatic in CI.

Changes:
- `backend/pyproject.toml`: `"fakeredis>=2.36.2"` removed from `[project] dependencies` and added,
  with the same bound, to `[dependency-groups] dev`.
- `backend/uv.lock`: refreshed with `uv lock` (no `--upgrade`). Only the group membership changed
  (the package entry of `medhub-backend` moves `fakeredis` from `dependencies` to
  `[package.dev-dependencies]`, and from `requires-dist` to `requires-dev`); `fakeredis` stays at
  2.36.2 and no package changed version.
- `.github/workflows/ci.yml`: job `build`, step "Check production dependency set" now also fails
  when `fakeredis` is present in the built backend image (TS-013 TC-013.8). The command was run
  against the unfixed image first and exited 1. The `backend-quality` job gained the step "Check
  the lock file is current" (`uv lock --check`, TS-013 TC-013.7), a follow-up from the QA review of
  TASK-157.
- `docs/soup/SOUP-018-fakeredis.md`: `obsolete`, version 1.1, approval record cleared, change-log
  entry. TS-013 (TC-013.7, TC-013.8) and ADD-024 (step description) updated.

Why the dev group and not removal: the tests still use `fakeredis` as the Redis substitute
(TS-001), and CI installs with `uv sync --frozen`, which includes the `dev` group.

Verification (TS-013 TC-013.8), reproducible from the repository root:

```sh
cd backend
uv lock --check                                                    # exit 0
uv run pytest -q                                                   # 496 passed
UV_PROJECT_ENVIRONMENT="$(mktemp -d)/venv" sh -c \
  'uv sync --frozen --no-dev && "$UV_PROJECT_ENVIRONMENT/bin/python" -c "import importlib.util, sys; import boto3; sys.exit(importlib.util.find_spec(\"fakeredis\") is not None)"; echo "exit=$?"'   # exit=0
cd .. && docker build -t medhub-backend:ci ./backend
docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.util, sys; import boto3; sys.exit(importlib.util.find_spec('fakeredis') is not None)"   # exit 0
```

Negative check: the same command run against the image built before the manifest change exited 1,
so the step fails when `fakeredis` is in the production image. The Docker Build job itself cannot
be run locally; it is confirmed on the branch head after the push.

## Source

Found while splitting the SOUP list into one record per component (2026-10-21).
