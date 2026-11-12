---
id: "PRB-038"
type: problem-report
title: "POSTGRES_PASSWORD is required by Compose but absent from .env.example"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-11-12"
criticality: minor
links: []
tags: ["configuration-management", "infrastructure"]
---

# PRB-038 — POSTGRES_PASSWORD is required by Compose but absent from .env.example

## Observed

`infra/docker-compose.yml` sets `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}` on the `postgres` service,
and `infra/DEPLOY.md` lists `POSTGRES_PASSWORD` among the required variables, but
`infra/.env.example` does not define it (it defines only `DATABASE_URL`, with the password
`changeme`). Every `docker compose` invocation from a copy of the example prints
`The "POSTGRES_PASSWORD" variable is not set. Defaulting to a blank string.` (observed 2026-10-22,
local `infra/.env`, which also lacks it).

## Impact

- On a fresh `postgres_data` volume the `postgres` image is expected to refuse to initialise with an
  empty superuser password (not run: it would require deleting the developer's volume). A new
  deployment following `.env.example` would not come up.
- On an existing volume the password set at first initialisation stays in force, which hides the
  gap, and `DATABASE_URL` and `POSTGRES_PASSWORD` can silently disagree.

## Investigation

Re-checked against the tree on 2026-11-12. **The observed defect is no longer present.** CR-004
fixed it as a side effect of PRB-007 (TASK-203, commit `4b1daf5`), without a `resolves` link to
this PRB:

- `infra/.env.example:14-18` defines `POSTGRES_PASSWORD=`. The value is deliberately empty, and the
  comment above it gives the generation command (SR-041 AC 4: the template holds no value for any
  secret).
- `infra/docker-compose.yml:130` sets
  `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}`. An unset or empty value
  now stops every `docker compose` invocation with a message that names the setting (SR-041 AC 2).
  Before, Compose only warned and fell back to a blank password. `infra/tests/test_ci_compose_env.py:81-84`
  and `infra/tests/test_compose_secrets.py` check this.
- `infra/DEPLOY.md:27-34` states the relationship. Since CR-004 (TASK-191, ADR-0017) the password
  inside `DATABASE_OWNER_URL` must equal `POSTGRES_PASSWORD`, and the runtime `DATABASE_URL` uses a
  different role and password. So this PRB's proposed resolution ("same placeholder as
  `DATABASE_URL`") is superseded.
- Fresh-project bring-ups from the empty template with generated secrets have already passed: the
  TASK-191 smoke run on the fresh project `task191` (59 passed, 0 failed) and TASK-202 (78 passed,
  0 failed). No fresh-volume bring-up has been recorded against this PRB.
- What remains is a records gap. No CR `resolves` PRB-038, so it stays `open` although the
  behaviour is fixed. CR-005 resolves it with verification only, and no code change is planned.

## Safety evaluation

No hazard is realized. At the current tree a missing or empty password fails loudly at bring-up
and never falls back to a blank superuser password. RISK-001 and the control of SR-041 AC 2 hold.
Hence `minor`, unchanged. No `release` record exists, so no released version is affected and no
notification is needed.

## Proposed resolution

Add `POSTGRES_PASSWORD` to `infra/.env.example` with the same placeholder as `DATABASE_URL`, and
state in DEPLOY.md that the two must match. Needs a task.

## Source

Found by the software developer while running TASK-155 verification (AC-5); out of scope for CR-001.

## Version history

- 1.1 (2026-11-12) — `## Investigation` added for CR-005 (Specify stage): the defect was fixed by CR-004 TASK-203 (commit `4b1daf5`) with no `resolves` link; CR-005 resolves it by verification (fresh-volume bring-up). Criticality unchanged.
