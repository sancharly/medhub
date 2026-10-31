---
id: "TASK-203"
type: task
title: "Empty environment template, required secrets in Compose, and a secret generation guide"
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
  - target: "RISK-005"
    relation: mitigates
  - target: "PRB-007"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "TASK-197"
    relation: relates_to
  - target: "ADD-026"
    relation: relates_to
tags: ["security", "deployment", "cr:CR-004", "control:design", "control:information"]
---

# TASK-203 — Empty environment template, required secrets in Compose, and a secret generation guide

- **Software item / unit:** SI-DEPLOY `U-DEP-Compose`, `U-DEP-EnvTemplate` (ADD-026).
- **PRB:** PRB-007. **CR:** CR-004.
- **Depends on:** TASK-140, TASK-197 (same files; the shared placeholder list). Ordered before
  TASK-191, TASK-198 and TASK-196, which edit the Compose file and template after it.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (`infra/docker-compose.yml`, `infra/.env.example`, `infra/DEPLOY.md`,
  `backend/tests/test_env_example.py`, 1 new infra test; TS-015)
- **Needs:** a Docker host for the bring-up checks.

## Objective

SR-041 AC 2 and AC 4: no default for any secret setting in the deployment definition; bring-up
fails with a message naming an unset or empty one; the template holds no secret value; the guide
says how to generate each. PRB-007 Investigation: `POSTGRES_PASSWORD` is unguarded and missing
from the template; `DATABASE_URL`, `SMTP_PASSWORD` and `AT_REST_ENCRYPTION_KEY` ship placeholders;
`backend` and `celery-worker` take everything from `env_file` without a guard.

## Implementation detail

1. `infra/docker-compose.yml`: `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}`;
   in `backend` and `celery-worker` `environment:`, every secret setting with a `:?` guard
   (`DATABASE_URL`, `AT_REST_ENCRYPTION_KEY`, the object-store keys). `SMTP_PASSWORD` cannot be
   conditionally required by Compose; it is passed through without a default and TASK-197's rule
   refuses it when `SMTP_USER` is set (Q-5). No `:-` default on any secret.
2. `infra/.env.example`: `POSTGRES_PASSWORD=`, `DATABASE_URL=`, `SMTP_USER=`, `SMTP_PASSWORD=`,
   `AT_REST_ENCRYPTION_KEY=` (all empty), each preceded by its generation command.
3. `infra/DEPLOY.md`: a "Secret settings" table (setting, used by, how to generate, rotation
   reference) that is the definition SR-041's Description points to.
4. `backend/tests/test_env_example.py`: the exception list that tolerates `changeme` in the
   database URL and SMTP password (`test_env_example.py:51-52`) is removed.

## Tests (write first)

- `infra/tests/test_compose_secrets.py`: parse the Compose file; every secret setting in every
  service that uses it is `${VAR:?…}`; no secret has `:-`; the secret list is the one in
  `backend/app/core/secret_settings.py`.
- `backend/tests/test_env_example.py`: every secret setting is present and empty; no value of
  the shared placeholder list appears anywhere in the file.
- Bring-up (manual, recorded): with `POSTGRES_PASSWORD` unset, `docker compose config` fails with
  a message naming it; same for `DATABASE_URL` and `AT_REST_ENCRYPTION_KEY`.

## Acceptance criteria

- [ ] SR-041 AC 2: no default for any secret; unset or empty stops bring-up naming the setting
      (`infra/tests/test_compose_secrets.py`, bring-up record).
- [ ] SR-041 AC 4: the template has no secret value and the guide says how to generate each
      (`backend/tests/test_env_example.py`, `infra/DEPLOY.md` review).

## Verification

```sh
cd infra && python3 -m pytest tests -v
cd backend && uv run pytest tests/test_env_example.py -v
env -u POSTGRES_PASSWORD docker compose -f infra/docker-compose.yml --env-file /dev/null config   # expect the named error
```

## Records

- **TS-015**: TC-015.2 (Compose guards, bring-up refusal), TC-015.4 (template, guide).
- **PRB-007**: Resolution started; `resolved` by TASK-196, the last PRB-007 task.

## Definition of Done

- [ ] Infra and backend tests pass; bring-up refusals recorded.
- [ ] TS-015 `in_review`.
- [ ] `traceability-check` shows no error for TASK-203, TS-015, SR-041.
