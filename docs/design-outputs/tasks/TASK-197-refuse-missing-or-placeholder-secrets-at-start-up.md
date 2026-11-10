---
id: "TASK-197"
type: task
title: "Refuse missing or placeholder secret settings at start-up of the backend and the worker"
status: approved
version: "1.1"
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

- [x] SR-041 AC 3: backend and worker refuse placeholders and a wrong-length key, naming the
      setting and never the value (`backend/tests/core/test_secret_settings.py`,
      `backend/tests/test_lifespan.py`).
- [x] CR-004 Q-5: SMTP without authentication starts; with a user and no password it is refused
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

- [x] Backend suite passes; coverage ≥ 85 %.
- [x] TS-015 `in_review`.
- [x] `traceability-check` shows no error for TASK-197, TS-015, SR-041.

## Version history

- 1.1 (2026-10-31) — Implemented (Software Developer role); handed to QA, `in_review`. See
  Implementation notes.
- 1.1 (2026-10-31) — QA review: APPROVED (`in_review → approved`); TS-009 1.8 and TS-015 1.0 approved. Findings 1 to 4 non-blocking; carried requirements for TASK-191, TASK-193/195 and TASK-196 listed in the review.

## Implementation notes

- `backend/app/core/secret_settings.py` (new): `SECRET_SETTINGS`, `KNOWN_DEFAULTS` (weak words),
  `KNOWN_PLACEHOLDERS` (weak words plus `change-me`, `change-me-to-a-random-32-byte-secret`,
  `change-me-to-a-random-32-byte-key!`), the prefix rule (any value starting `change-me`, a
  superset of `change-me-to-`), `check_value`, `check(env)`, `secret_values(env)`,
  `settings_env()` and `enforce(env=None)` (`SystemExit`, messages name settings only). It does
  not import `config` at module level, so the object-store preflight (`python -m
  app.core.object_store_credentials`) still runs with no application settings.
- `object_store_credentials.py` now delegates to `check_value` and re-exports `KNOWN_DEFAULTS`
  (one list; messages and the 16-character minimum unchanged).
- `config.py`: `smtp_user` defaults to empty, `smtp_password` is optional and required by a model
  validator when a user is set (Q-5). QA item 2: `extra="ignore"` replaced by the default (forbid)
  plus a `mode="before"` validator that drops only `session_signing_key`, case-insensitively, so a
  stale line still starts the app and a typo such as `TRUSTED_PROXIE` in `.env` fails. Added
  `hide_input_in_errors=True` so a pydantic error (for example the SMTP rule) never echoes a
  setting value.
- `main.py` lifespan calls `enforce()` first; `celery_app.py` connects it to `worker_init` and
  `beat_init`; `email_tasks.py` copes with `smtp_password` being `None`.
- QA item 1 (from TASK-140): the TC-009.12 flow scan in `test_audit_no_secrets.py` takes its
  forbidden values from `secret_values(settings_env())`, the same list the start-up rule uses, plus
  a negative-control test that writes every configured secret into an audit row. Docstring updated;
  TS-009 1.8 `in_review`.
- Deviations: (a) the prefix rule is `change-me` rather than `change-me-to-`, so a local
  `change-me-generate-…` value is refused as well; (b) a `DATABASE_URL` without a password is
  refused (a secret that is missing); (c) `crypto.py` is unchanged and keeps its lazy check, whose
  decoding the start-up check mirrors.
- Test environments with a key that did not decode to 32 bytes were changed to ones that do:
  `backend/tests/test_config.py`, `test_lifespan.py`, `backend/modules/dicom_viewer/tests/conftest.py`
  and `.github/workflows/ci.yml` (both jobs).
- Not done, by design: the template and Compose guards (TASK-203), the non-root image (TASK-198).
  `infra/.env.example` still ships its placeholders until TASK-203, so an operator who copies it
  unchanged is now refused at start-up, which is the intended behaviour.
- Records: TS-015 1.0 new (`in_review`); TS-009 1.8 `in_review`; PRB-007 interim note (stays
  `open`). ADD-026 already names `U-DEP-SecretRule` (approved record, not edited).

## QA review (QA engineer, 2026-10-31): APPROVED

No CRITICAL or HIGH finding. TASK-197 `in_review → approved`; TS-009 1.8 and TS-015 1.0
`in_review → approved`. TASK-140 QA findings 1 and 2 are closed: the flow scan takes its forbidden
values from `secret_values(settings_env())`, and the default `forbid` is back, with only the retired
key dropped.

### Findings (non-blocking)

1. **MEDIUM — no test guards `hide_input_in_errors`** (`backend/app/core/config.py:23`).
   - The control: with the flag removed, all 125 targeted tests still pass.
     `test_smtp_user_without_password_is_refused_without_echoing_values`
     (`backend/tests/test_config.py:107`) passes either way, because pydantic truncates the
     model-level `input_value`.
   - The leak is real. With the flag off, `DATABASE_URL=mysql://u:SENTINEL@h:5432/d` puts
     `SENTINEL` in the `ValidationError` text. With the flag on, it does not.
   - → Add that case to `test_config.py`: assert `SENTINEL` is not in `str(exc.value)`. Name the
     test in TS-015 TC-015.3.
2. **LOW — the backend container migrates before the refusal.** `backend/entrypoint.sh:4` runs
   `alembic upgrade head` before gunicorn, and `app/db/alembic/env.py:22` reads `DATABASE_URL`
   without `enforce()`. With a placeholder database password, the schema is migrated and only then
   is the API refused. The API never serves, and no migration uses the field key.
   → Call `enforce()` at the top of `app/db/alembic/env.py`. That covers this entrypoint and the
   `db-migrate` service of TASK-191 (carried requirement C1).
3. **LOW — the PRB-007 interim note is imprecise** (`docs/problem-reports/PRB-007-*.md:76-83`).
   - It says the optional owner URL, retired keys and SSE key are refused when "unset". They are
     checked only when set.
   - It says the worker refuses. That holds for a Celery process (verified), but the Compose
     `celery-worker` container does not run Celery (pre-existing issue P1).
   - → Reword both points when PRB-007 is next edited, at the latest in TASK-203.
4. **LOW — the flow scan's database-password sentinel is weak.** The baseline `DATABASE_URL`
   password is `pass` (`backend/tests/conftest.py:15`), and the scan does a case-sensitive
   substring match. It passes today only because actions are upper case (`PASSWORD_CHANGED`).
   → Use a distinctive baseline password, e.g. `test-db-pw-7f3a`.

### Pre-existing issue (not caused by this task)

- **P1 — the `celery-worker` container runs gunicorn, not Celery.** The image's
  `ENTRYPOINT ["./entrypoint.sh"]` ignores its arguments: there is no `exec "$@"`. So the Compose
  `command: celery -A app.workers.celery_app worker` (`infra/docker-compose.yml:206`) is dropped.
  The container migrates and serves the API instead. No e-mail, retention or session task runs,
  and the `worker_init` refusal never runs in the started stack.
  → Open a PRB (problem-report-resolution). It affects the SR-041 AC 6 started-stack check
  (TASK-198/203) and every worker requirement.

### Carried requirements (for later CR-004 tasks)

- **C1, TASK-191:** the `db-migrate` service carries `DATABASE_OWNER_URL`. It must run `enforce()`
  before alembic (see finding 2), and the owner URL must be required in that process, not checked
  only when present.
- **C2, TASK-196:** `OBJECT_STORE_SSE_KEY` becomes a `Settings` field.
  - Move it into `_REQUIRED` for the processes that use it, read it in `settings_env()` from
    `Settings`, not `os.environ`, and keep the base64 32-byte check.
  - Add the SR-041 AC 5 refusal when it equals `AT_REST_ENCRYPTION_KEY`.
  - Give the preflight both keys.
- **C3, TASK-193/195:** when the key id and the retired keys become `Settings` fields, read them in
  `settings_env()` from `Settings`. Read from `os.environ`, a value in a local `.env` would be
  refused as extra under `forbid`. Keep the per-key 32-byte check.

### Checks (questions 1 to 8)

1. **Coverage.**
   - `SECRET_SETTINGS` covers every secret `Settings` holds: the DB password,
     `AT_REST_ENCRYPTION_KEY`, `SMTP_PASSWORD` and both object-store keys.
   - `REDIS_URL` has no password in Compose (`redis-server` without `requirepass`), so it is out of
     scope.
   - Modules read no secret.
   - The engine is lazy (`get_engine` is `lru_cache`d), so no secret is read at import, except
     pydantic validation in `celery_app.py:31`, which runs before `worker_init` and is
     input-hidden.
   - Paths without the lifespan: alembic (finding 2). `scripts/setup_test_data.py` and
     `migrate_object_store.py` are operator tools with their own environment; `export_openapi`
     uses no secret. These are out of scope.
2. **`os.environ` reads.** They are consistent for now. Making those settings required is carried
   as C1 to C3.
3. **Messages.**
   - Real gunicorn with placeholders exits 3: "Application startup failed", the master shuts down,
     and only setting names are printed.
   - Real `celery worker` and `celery beat` exit 1 with the names only. Beat logs the refusal at
     WARNING.
   - Celery's dispatcher catches `Exception`, not `SystemExit`, so the refusal propagates.
   - No probe value (`SECRETVALUE…`, `changeme`, the key) appears in any log.
4. **Validator and `forbid`.**
   - Process environment variables are never extra.
   - Compose `env_file:` and the CI `set -a; . infra/.env` both give process env, and the image has
     no `.env`.
   - The local `backend/.env` holds only field names plus the dropped key.
   - Nothing breaks.
5. **Prefix `change-me`.** Generated secrets (hex, base64, urlsafe base64) start with it with
   probability about 64^-9, so it does not matter in practice. It is stricter than SR-041's
   `change-me-to-`, and the deviation is recorded.
6. **Password-less `DATABASE_URL`.** The only supported deployment is Compose with password auth;
   no peer, socket or IAM setup is documented. Refusing it is accepted.
7. **Template.** `infra/smoke-test.sh` only runs `docker compose config` on the copied template and
   skips its runtime checks without a stack. CI never starts the backend from the template; the
   object-store job writes its own `.env`. Nothing breaks. An operator's unedited copy is refused,
   as intended until TASK-203.
8. **Records.**
   - TS-015 meets the TS contract: `verifies` SR-041, and it has scope, environment, cases,
     §5.5.3 criteria and history.
   - TS-009 1.8 TC-009.12 is accurate.
   - Every historical template secret value (`git log -p infra/.env.example`) is classified as a
     placeholder or empty.
   - The PRB-007 note has the two inaccuracies in finding 3.

### Negative controls (scratch copy)

| Mutation | Result |
|---|---|
| Value interpolated into the placeholder message | the placeholder cases fail (12 or more) |
| `hide_input_in_errors` removed | all pass (finding 1) |
| `_drop_retired_keys` disabled | `test_stale_session_signing_key_is_ignored` fails |
| Lifespan `enforce()` removed | `test_lifespan_refuses_a_placeholder_secret_before_starting` fails |
| Celery handler `enforce()` removed | `test_worker_init_handler_stops_on_a_placeholder` fails |

### Verification run

| Command | Result |
|---|---|
| `uv run pytest tests/core tests/test_lifespan.py tests/test_config.py tests/workers tests/audit` | 333 passed |
| `uv run pytest --cov=app --cov-fail-under=85` | 1052 passed, 4 skipped; coverage 94.13 % |
| `uv run pytest modules/dicom_viewer/tests` | 25 passed |
| `uv run ruff check . && uv run black --check . && uv run mypy app` | clean; 246 files unchanged; no issues in 128 files |
| `cd infra && python3 -m unittest discover -s tests` | 37 OK |
| OpenAPI export vs `backend/openapi/openapi.json` | identical |
| Real gunicorn, `celery worker`, `celery beat` with placeholder secrets | exit 3, 1 and 1; names only, no value |
| traceability (TASK-197, TS-009, TS-015, PRB-007, SR-041) | 0 errors. 3 warnings: W5 TP-001 → TS-009 `in_review` (cleared by this approval); W6 CR-002 → SOUP-022 and SOUP-023 obsolete (pre-existing). After approval: 0 errors; new W5 TASK-197 → ADD-026 `in_review`. ADD-026 is `in_review`, not approved as the Implementation notes say; its human gate is pending |
