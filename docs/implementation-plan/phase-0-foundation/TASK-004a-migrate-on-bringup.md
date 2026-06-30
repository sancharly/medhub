# TASK-004a — Database migration on bring-up (remediation)

- **Phase:** 0 — Foundation
- **Implements / restores:** SR-001.1, SR-003; remediates TASK-004, TASK-005
- **Depends on:** TASK-004, TASK-011 (migrations)
- **Branch:** `feature/migrate-on-bringup`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-004 verdict **FAIL**; `SMOKE-RESULTS.md` F5

## Objective

There is **no database migration step anywhere** — not in the backend `Dockerfile`/entrypoint, not in
`infra/docker-compose.yml`, not in the app lifespan. The runtime image also lacks `uv` and does not
copy `alembic.ini`, so the `DEPLOY.md` manual `uv run alembic upgrade head` fails two ways. A fresh
`docker compose up` therefore comes up with an empty schema and every DB endpoint 500s.

## Implementation detail

- Copy `alembic.ini` into the backend image and ensure `alembic` is runnable in the runtime stage
  (it is a main dependency; expose it on PATH).
- Add automated migration on bring-up: either a one-shot `migrate` compose service that runs
  `alembic upgrade head` and that `backend` depends on, or a backend entrypoint that runs it before
  Gunicorn. Must be idempotent and safe under restart.
- Run migrations (or `create_all`) in the CI `backend-tests` job / conftest before DB integration tests
  (TASK-005 gap).
- (Optional, related infra) auto-create the MinIO bucket and fail fast if the at-rest/KMS key is the placeholder.

## Acceptance criteria

- [x] A fresh `docker compose up` on empty volumes yields a fully-migrated schema; `POST /auth/login`
  and other DB endpoints work without any manual step.
- [x] Migration step is idempotent across restarts.
- [x] CI runs migrations before DB-backed tests.

## Definition of Done

- [x] Lint/build pass; backend + frontend images build
- [x] Bring-up smoke confirms migrated schema + a working login end-to-end (extend `infra/smoke-test.sh`)
- [x] Traceability row updated (SR-001 → TASK-004a)
- [x] Security review N/A

## Implementation notes (2026-06-30)

- `backend/entrypoint.sh` — runs `alembic upgrade head` then `exec gunicorn`; idempotent (alembic no-ops when schema is current).
- `backend/Dockerfile` — builder stage copies `alembic.ini` and `modules/`; runtime stage copies both from builder plus `entrypoint.sh`; non-root `medhub` user; `ENTRYPOINT` replaces `CMD`.
- `infra/docker-compose.yml` — `createbuckets` (minio/mc) service auto-creates the MinIO bucket; backend `depends_on: createbuckets`; all `:-default` secret fallbacks removed (POSTGRES_PASSWORD, OBJECT_STORE_ACCESS_KEY, OBJECT_STORE_SECRET_KEY, AT_REST_ENCRYPTION_KEY); backend healthcheck added.
- `.github/workflows/ci.yml` — `Run database migrations` step added before pytest in `backend-tests`.
- `infra/smoke-test.sh` — section 9 checks `POST /auth/login` returns 401/422 (not 500) to prove schema is migrated.
