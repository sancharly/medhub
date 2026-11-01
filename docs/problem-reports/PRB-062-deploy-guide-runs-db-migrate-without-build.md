---
id: "PRB-062"
type: problem-report
title: "DEPLOY.md runs db-migrate without --build, so an upgrade can skip the new migrations"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-01"
updated: "2026-11-01"
criticality: minor
links: []
tags: ["deployment", "documentation", "hazard:availability", "cr:CR-004"]
---

# PRB-062 — DEPLOY.md runs db-migrate without --build, so an upgrade can skip the new migrations

## Observed

Found by the Software Developer during the TASK-194 rehearsal (2026-11-01). `infra/DEPLOY.md`
section 6 and step 3 of "Upgrading an installation that connects as the owner" told the operator to run
`docker compose -f infra/docker-compose.yml up db-migrate`. `db-migrate` is built from the backend
source, but `up` without `--build` reuses an image that already exists. After a `git pull`, that
is the image of the previous release: it contains none of the new migrations and exits 0.

In the rehearsal, `up db-migrate` on the new tree printed `database roles applied` and exited 0 while the
database stayed at 0009; `up --build db-migrate` then ran 0009 to 0010. A second, related fact found by
QA: `docker compose up` returns exit code 0 even when the `db-migrate` container exits 1 (Compose
v2.20.2), so a refusal is also reported as success unless `--exit-code-from db-migrate` is given.

## Impact

For the documented upgrade, the later step 4 (`up -d --build`) rebuilds `db-migrate` and runs the pending
migrations before the backend starts, so the new backend is not started against the old schema. What
goes wrong:

- the checkpoint of step 3 is falsely green (exit 0, `database roles applied`, nothing migrated);
- section 6 used alone after a `git pull` skips the new migrations for real, and a script written as
  `up db-migrate && up -d` is told success after a refusal.

Without migration 0010 the symptom is HTTP 500 on the first clinical read (CR-004 D-5), not a failed
deployment. Documentation defect; the code is correct.

## Safety evaluation

Contributes to RISK-007 (clinical information unavailable) only through an operator following section 6
alone on an upgrade. No release exists (CR-004 A-1) and there was no occurrence outside the rehearsal.
Criticality **minor**: before this fix nothing in the stack reported it except the first clinical
read (HTTP 500); no data is changed or lost.

## Resolution

Fixed in TASK-194 (human decision, CR-004 D-7, 2026-11-01).

- `infra/DEPLOY.md`: every command that runs `db-migrate` alone is now
  `docker compose -f infra/docker-compose.yml up --build --exit-code-from db-migrate db-migrate` (section 6,
  step 3 of the owner upgrade, and the migration 0010 section), and section 6 explains both flags.
- `infra/tests/test_deploy_db_migrate_commands.py` fails when such a line lacks `--build` or
  `--exit-code-from db-migrate`.
- `infra/smoke-test.sh` now checks, on a started stack, that `alembic_version` equals the head revision
  of the tree, so a skipped migration cannot pass. Checked on a scratch stack: 65 passed at the head; with
  `alembic_version` set to 0009 the new check failed and named the command to run.

## Source

TASK-194 rehearsal, scratch project `task194`.

## Version history

- 1.0 (2026-11-01) — Created from TASK-194. `open`, `minor`.
- 1.1 (2026-11-01) — TASK-194 round 2: impact corrected, resolution written, fixed and verified. `open` → `resolved`.
