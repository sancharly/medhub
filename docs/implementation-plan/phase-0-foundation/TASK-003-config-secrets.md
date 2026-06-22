# TASK-003 — Config & secrets management

- **Phase:** 0 — Foundation & toolchain
- **Software item / unit:** SI-API / `app.core.config` (cross-cutting §8.11)
- **Implements:** NFR-007, §8.11 (Configuration & secrets)
- **Depends on:** TASK-002 (must be merged first)
- **Branch:** `enabler-story/config-secrets`
- **Status:** Completed

## Objective

Provide one typed, twelve-factor configuration surface (`Settings`) that every backend item reads through, with all secrets injected from the environment at deploy time and **nothing sensitive committed**. This is the cross-cutting configuration/secrets concept (§8.11) and the deployment operational rule that signing/crypto/DB/SMTP keys are operator-managed env values (07-deployment-view) supporting NFR-007.

## Interfaces to honor

- Provides an in-process `Settings` object (and a cached `get_settings()` provider) consumed by all items via FastAPI dependency injection. App code reads config **only** through this object — never `os.environ` directly (so the source of truth is single and typed).
- Must **not** print, log, serialize, or expose secret values (no secrets in `/healthz`, error bodies, or logs — consistent with TASK-002 logging). Must **not** ship real secrets; only an `.env.example` with placeholder values is committed.

## Implementation detail

- Files to create / modify:
  - `backend/app/core/config.py` — `Settings(BaseSettings)` using **pydantic-settings** (Pydantic v2). Fields grouped and typed: `environment` (`local|staging|production`), `database_url` (`PostgresDsn`), `redis_url`, `object_store_endpoint`/`object_store_access_key`/`object_store_secret_key`/`object_store_bucket` (MinIO), `session_signing_key` (`SecretStr`), `smtp_host`/`smtp_port`/`smtp_user`/`smtp_password` (`SecretStr`), `at_rest_encryption_key` placeholder (`SecretStr`, used by TASK-013), `cors_origins`. Secrets use `SecretStr` so they never render in `repr`/logs. Add `get_settings()` cached with `functools.lru_cache`.
  - Modify `backend/app/main.py` (TASK-002 seam): call `get_settings()` at startup; pass non-secret values (e.g. `environment`, `cors_origins`) where needed. Do not log secret fields.
  - `infra/.env.example` — every key above with **placeholder** values and inline comments; this is the documented contract of required env vars (NFR-007, §8.11).
  - Confirm `.gitignore` (TASK-001) excludes `.env`, `*.env`, `infra/.env`; rely on the TASK-001 pre-commit secret-block hook.
- Libraries: `pydantic-settings` (exact stack — Pydantic v2 family).
- Config keys: those listed above are the canonical set; later tasks extend `Settings` additively rather than reading env directly.
- Error cases: missing required env var → app **fails fast at startup** with a clear, non-secret validation message (pydantic-settings `ValidationError`); never falls back to an insecure default for a secret.

## Tests (write first — TDD, CLAUDE.md §4)

- `backend/tests/test_config.py`:
  - Given a complete env, `Settings` loads and exposes typed values.
  - A missing required key (e.g. `database_url`) raises a validation error at construction (fail-fast).
  - `repr(settings)` and `str(secret_field)` do **not** reveal secret values (`SecretStr` masks; verifies "no secret disclosure", NFR-007).
  - `get_settings()` is cached (same instance across calls).
- `backend/tests/test_env_example.py`: every field declared on `Settings` (excluding those with safe defaults) has a corresponding key in `infra/.env.example`, so the documented contract stays in sync.

## Acceptance criteria

Distilled from NFR-007 and §8.11 / 07-deployment-view operational notes:

- [ ] All configuration is read from the environment through a single typed `Settings`; no direct `os.environ` reads in app code.
- [ ] Secrets (DB, object-store keys, session signing key, SMTP, at-rest key) are env-injected and never committed; only `infra/.env.example` with placeholders is in the repo.
- [ ] Secret values are masked in `repr`/logs (`SecretStr`) and absent from `/healthz` and error bodies.
- [ ] Missing required configuration fails fast at startup with a clear, non-secret message.
- [ ] `.env`/secret files are blocked from commits (TASK-001 hook) and ignored by git.

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (no contract change expected)
- [ ] Audit events emitted for security-relevant actions (N/A)
- [ ] Traceability matrix row updated (NFR-007, §8.11 → TASK-003 → config tests)
- [ ] Security review completed (N/A here; the auth/session review gate is SR-031.6 in later tasks)
