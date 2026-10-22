---
id: "TASK-158"
type: task
title: "Move fakeredis to the dev dependency group"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
links:
  - target: "SR-028"
    relation: implements
  - target: "TASK-157"
    relation: relates_to
tags: ["soup", "configuration-management", "cr:CR-001", "issue:sancharly/medhub#26"]
---

# TASK-158 — Move fakeredis to the dev dependency group

- **Software item / unit:** SI-DEVINFRA `U-INF-Toolchain`, `U-INF-CIPipeline` (ADD-024); the
  backend runtime image
- **Depends on:** TASK-157 (same `pyproject.toml`, `uv.lock` and CI step; merge after it), as a
  `relates_to` link
- **Branch:** `bug/soup-pinning`

## Objective

Resolve PRB-033: `fakeredis` is a `[project]` runtime dependency although only the test suite
imports it, so an unused, unreviewed in-memory Redis imitation ships in the production image
(SOUP-018). Move it to the `dev` group so the production image no longer contains it, and retire
SOUP-018. No risk control depends on `fakeredis`. The change removes the misconfiguration path
toward RISK-005 and RISK-007 described in CR-001's risk impact, so the task has no `mitigates` link.

## Interfaces to honor

- The tests keep importing `fakeredis` (`tests/auth/test_session_service.py`,
  `tests/auth/test_lockout.py`, `tests/identity/test_erasure.py`, `tests/identity/test_lifecycle.py`).
  CI's `uv sync --frozen` installs the `dev` group by default, so they keep working. TS-001's
  environment statement ("fakeredis substitutes Redis") stays true.
- No file under `backend/app/` or `backend/modules/` may import it (none does today).

## Implementation detail

- `backend/pyproject.toml`: remove `"fakeredis>=2.36.2"` from `[project] dependencies`; add the
  same specifier to `[dependency-groups] dev`.
- `cd backend && uv lock` without `--upgrade`. In `git diff backend/uv.lock`, `fakeredis` must stay
  at 2.36.2 and move to the dev group. `sortedcontainers` may become dev-only. Any other version
  change is out of scope: revert it.
- `.github/workflows/ci.yml`, job `build`, step "Check production dependency set" (from
  TASK-157): extend the command to also fail when `fakeredis` is present:
  `docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.util, sys; import boto3; sys.exit(importlib.util.find_spec('fakeredis') is not None)"`.
- **SOUP-018** → `status: obsolete`, `version` 1.1, approval record removed. Replace the PRB-033
  note with "No longer shipped: moved to the `dev` dependency group (PRB-033, CR-001). Development
  tooling that is not shipped is not SOUP." Change log:
  `2026-10-22 — removed from the runtime dependency set (dev group only); record obsolete; PRB-033, CR-001`.
  No anomaly review is required for an obsolete record (TASK-154 skips it).
- **Do not** edit RISK-010 here. Its `relates_to` link to SOUP-018 is removed in TASK-159
  together with the rest of the RISK-010 revision, so the approved record is revised once. Until
  then, a `traceability-check` warning about a link to an obsolete record is expected.
- **TS-013** (at 1.2): extend `TC-013.8` so its expected result also says `fakeredis` is absent
  from the production image.
- **ADD-024** (at 1.1): the dependency-set step description includes the `fakeredis` absence check.
- **PRB-033** → `status: resolved`, `version` 1.1. Rewrite its `## Resolution` (today a proposal)
  as the actual resolution: the changed files, and the verification (TC-013.8, the local `--no-dev`
  check below, backend suite passing).

## Tests (write first)

Extend the CI step first and run it against the current image: it must exit 1 while `fakeredis`
is still a runtime dependency. After the manifest change it exits 0.

## Acceptance criteria

- [ ] CR-001 **AC-9**: `fakeredis` absent from `[project] dependencies`, present in `dev`;
      `uv.lock` refreshed; a `uv sync --frozen --no-dev` environment does not contain it.
- [ ] CR-001 **AC-10**: SOUP-018 `status: obsolete`, bumped `version`, change-log entry citing
      PRB-033 and CR-001.
- [ ] CR-001 **AC-17** (PRB-033 part): PRB-033 `resolved` with its `## Resolution`.

## Verification

```sh
cd backend && uv lock --check
cd backend && UV_PROJECT_ENVIRONMENT="$(mktemp -d)/venv" sh -c 'uv sync --frozen --no-dev && "$UV_PROJECT_ENVIRONMENT/bin/python" -c "import importlib.util, sys; import boto3; sys.exit(importlib.util.find_spec(\"fakeredis\") is not None)"'; echo "exit=$?"   # expect 0
docker build -t medhub-backend:ci ./backend && docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.util, sys; import boto3; sys.exit(importlib.util.find_spec('fakeredis') is not None)"
cd backend && uv run pytest
```

## Definition of Done

- [ ] Backend lint, type check and suite pass; CI Docker Build job green
- [ ] SOUP-018 `obsolete`; TS-013 and ADD-024 `in_review`; PRB-033 `resolved`
- [ ] `traceability-check` shows no error for the touched records (the RISK-010 → SOUP-018
      warning is expected until TASK-159)
