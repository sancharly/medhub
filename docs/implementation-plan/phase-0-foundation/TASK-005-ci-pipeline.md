# TASK-005 — CI pipeline

- **Phase:** 0 — Foundation & toolchain
- **Software item / unit:** — / — (process enabler)
- **Implements:** NFR-006, SR-028
- **Depends on:** TASK-001 (must be merged first)
- **Branch:** `enabler-story/ci-pipeline`
- **Status:** Completed

## Objective

Automate the IEC 62304 implementation-and-integration gates as a CI pipeline that runs on every PR: lint, type-check, unit tests with a coverage gate, OpenAPI lint, and build. This enforces NFR-006 (controlled, repeatable lifecycle activity outputs) and supports SR-028 (each requirement traceable to a passing test) by making the test suite a merge gate.

## Interfaces to honor

- Runs the **exact same commands** developers run locally (TASK-001/002) so CI and local results are identical; reuses the pinned tool versions and the committed lockfiles (`uv.lock`, `package-lock.json`).
- Lints the generated OpenAPI document with `npx @redocly/cli lint` ([api-design.md](../../specifications/api-design.md) validation rule, NFR-006 interface definition).
- Must **not** introduce new lint/type rules or tooling beyond TASK-001's config (it consumes that config), and must **not** run against, deploy to, or require any real secret/environment — CI uses ephemeral/placeholder config only.

## Implementation detail

- Files to create:
  - `.github/workflows/ci.yml` (or the repo's CI provider equivalent) with jobs:
    1. **backend-quality** — `uv sync --frozen`; `uv run ruff check`; `uv run black --check`; `uv run mypy`.
    2. **backend-tests** — `uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=85`; spins up ephemeral `postgres:16`/`redis` services for any integration tests (later phases) using placeholder env.
    3. **frontend-quality** — `npm ci`; `npm run lint`; `npm run typecheck`.
    4. **frontend-tests** — `npm test -- --run` (Vitest).
    5. **openapi-lint** — generate `openapi.json` from the FastAPI app (a small `uv run python -m app.export_openapi` or equivalent) and run `npx @redocly/cli lint openapi.json`.
    6. **build** — `docker build` backend and frontend images (validates the TASK-004 Dockerfiles build), or `npm run build` + `uv build` if image build is deferred.
  - `backend/app/export_openapi.py` (small helper) — dumps `create_app().openapi()` to a file for the OpenAPI-lint job.
  - Add a CI status note/badge to `README.md`.
- Gates: pipeline **fails the PR** if any job fails (lint, types, tests, coverage `< 85%`, OpenAPI lint, build). Branch protection requires CI green before merge (per Git Flow, one PR per task).
- Config keys: CI-only placeholder env; never real secrets.
- Error cases: coverage below threshold, OpenAPI lint error, type error → red pipeline → merge blocked.

## Tests (write first — TDD, CLAUDE.md §4)

- The pipeline itself is the verification artifact; validate by:
  - A PR that intentionally fails lint/type/test/coverage/OpenAPI must show a **red** pipeline (negative check, recorded once).
  - A clean PR shows **green** across all jobs.
  - The coverage gate is asserted by config (`--cov-fail-under=85`) matching TASK-001's `fail_under`.
- No new application unit tests are added here beyond what TASK-001/002 provide.

## Acceptance criteria

Distilled from NFR-006 and SR-028:

- [x] CI runs on every PR and executes lint, type-check, unit tests, coverage gate, OpenAPI lint, and build.
- [x] CI uses the same pinned tool versions and committed lockfiles as local development (reproducible).
- [x] The coverage gate (≥ 85%) fails the build when unmet.
- [x] The generated OpenAPI document passes `@redocly/cli lint` in CI (interface definition, NFR-006).
- [x] A failing quality/test job blocks merge to `main` (supports requirement→test traceability, SR-028.4).
- [x] No real secrets or live environments are used in CI.

## Definition of Done

- [x] Lint + type-check pass (pipeline green on a clean PR)
- [x] Unit tests pass; coverage gate enforced (≥ 85%)
- [x] OpenAPI regenerated and re-linted (the dedicated CI job)
- [x] Audit events emitted for security-relevant actions (N/A — process)
- [x] Traceability matrix row updated (NFR-006, SR-028 → TASK-005 → CI gate)
- [x] Security review completed (N/A — no auth/session code)

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL → PASS (remediated 2026-06-30)
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation completed (TASK-004a):** `Run database migrations` step (`uv run alembic upgrade head`) added to `backend-tests` job in `.github/workflows/ci.yml` immediately before the pytest step.
