---
id: "TASK-197"
type: task
title: "Refuse missing or placeholder secret settings at start-up of the backend and the worker"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
links:
  - target: "SR-041"
    relation: implements
  - target: "SR-022"
    relation: implements
  - target: "RISK-001"
    relation: mitigates
  - target: "RISK-005"
    relation: mitigates
  - target: "RISK-011"
    relation: mitigates
  - target: "PRB-007"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "TASK-140"
    relation: relates_to
  - target: "ADD-026"
    relation: relates_to
tags: ["security", "deployment", "cr:CR-004", "control:protective"]
---

# TASK-197 — Refuse missing or placeholder secret settings at start-up of the backend and the worker

- **Software item / unit:** SI-DEPLOY `U-DEP-SecretRule` (ADD-026); settings.
- **PRB:** PRB-007 (placeholder secrets). **CR:** CR-004. **Decision:** CR-004 Q-5 (SMTP without
  authentication supported; `SMTP_PASSWORD` required only when `SMTP_USER` is set).
- **Depends on:** TASK-140 (removes `SESSION_SIGNING_KEY` from `config.py` first).
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (new `backend/app/core/secret_settings.py`; `config.py`, `main.py`,
  `workers/celery_app.py`, `core/object_store_credentials.py`; 1 new test file; TS-015)

## Objective

SR-041 AC 3: the backend and the worker refuse to start when a secret setting equals a known
placeholder (any case: `changeme`, `change-me`, a value starting `change-me-to-`, any value the
template ever shipped), and refuse an `AT_REST_ENCRYPTION_KEY` that does not decode to 32 bytes.
The error names the setting, never the value. Today the key is validated lazily, at first use
(PRB-004 Investigation), and nothing refuses placeholders (PRB-007 Investigation).

## Implementation detail

1. `backend/app/core/secret_settings.py`:
   - `SECRET_SETTINGS`: `DATABASE_URL` (password part), `DATABASE_OWNER_URL` (when present, i.e.
     in `db-migrate`), `SMTP_PASSWORD` (only when `SMTP_USER` is non-empty),
     `AT_REST_ENCRYPTION_KEY`, `AT_REST_ENCRYPTION_RETIRED_KEYS` (each key), `OBJECT_STORE_SSE_KEY`
     (when present), `OBJECT_STORE_ACCESS_KEY`, `OBJECT_STORE_SECRET_KEY`;
   - `KNOWN_PLACEHOLDERS`: every secret value `infra/.env.example` has shipped (from `git log -p
     infra/.env.example`: `changeme`, `change-me-to-a-random-32-byte-secret`,
     `change-me-to-a-random-32-byte-key!`, `minioadmin`, …) plus the prefix rule; the object-store
     list of `object_store_credentials.py` is folded in, so there is one list;
   - `check(env) -> list[str]` (one message per problem, each naming the setting) and
     `enforce(env)` (raises `SystemExit` with the messages).
2. `config.py`: `smtp_user: str = ""`, `smtp_password: SecretStr | None = None`; a model
   validator requires `smtp_password` when `smtp_user` is set (Q-5).
3. Call `enforce` in the API lifespan (`main.py`) before anything else, and on Celery's
   `worker_init` and `beat_init` signals (`celery_app.py`). `object_store_credentials.main()` uses
   the shared list.
4. `crypto.py` keeps its lazy check; the start-up check makes the 32-byte rule fail fast.

## Tests (write first)

`backend/tests/core/test_secret_settings.py`:

- each secret setting unset, empty, `changeme`, `CHANGEME`, `change-me`, `change-me-to-anything`
  and each historical template value → one message naming the setting; the value is not in the
  message or in captured logs;
- `AT_REST_ENCRYPTION_KEY` of 31 and 33 bytes → refused; 32 bytes → accepted;
- `SMTP_USER` empty and `SMTP_PASSWORD` unset → accepted; `SMTP_USER` set and password unset →
  refused (Q-5);
- the API lifespan and the Celery `worker_init` handler call `enforce` and stop on a placeholder
  (`backend/tests/test_lifespan.py` extended; a worker-init unit test).

## Acceptance criteria

- [ ] SR-041 AC 3: backend and worker refuse placeholders and a wrong-length key, naming the
      setting and never the value (`backend/tests/core/test_secret_settings.py`,
      `backend/tests/test_lifespan.py`).
- [ ] CR-004 Q-5: SMTP without authentication starts; with a user and no password it is refused
      (`backend/tests/core/test_secret_settings.py`).

## Verification

```sh
cd backend && uv run pytest tests/core tests/test_lifespan.py tests/test_config.py tests/workers -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
```

## Records

- **TS-015** (new, `verifies` SR-041): TC-015.3 (start-up refusal, Q-5). TASK-198 adds TC-015.1,
  TASK-203 TC-015.2 and TC-015.4, TASK-196 extends TC-015.3 (SSE key).
- **ADD-026** 1.0: confirm `U-DEP-SecretRule`.

## Definition of Done

- [ ] Backend suite passes; coverage ≥ 85 %.
- [ ] TS-015 `in_review`.
- [ ] `traceability-check` shows no error for TASK-197, TS-015, SR-041.
