# TASK-001 — Monorepo structure & tooling

- **Phase:** 0 — Foundation & toolchain
- **Software item / unit:** — / — (enabler)
- **Implements:** NFR-006, SR-028
- **Depends on:** none
- **Branch:** `enabler-story/monorepo-tooling`
- **Status:** Completed

## Objective

Establish the version-controlled monorepo skeleton and the developer toolchain so every later task lands in a fixed, lint-and-type-checked layout with reproducible builds. This is the substrate for the IEC 62304 implementation activity: controlled, traceable, version-controlled records (NFR-006, SR-028). No application behaviour is implemented here — only structure, tooling, and the conventions that make every subsequent task verifiable.

## Interfaces to honor

This task provides no runtime interface. It must materialize the **repo layout** exactly as defined in [TASK-TEMPLATE.md](../TASK-TEMPLATE.md) ("Repo layout") and lock the **exact stack** named there. It must **not** introduce any framework, language, or tool outside that stack list, and must **not** add application code (no models, routers, or React components) — those belong to later tasks.

## Implementation detail

- Files to create:
  - Root: `README.md` (build/run quickstart per NFR-006), `.gitignore` (Python, Node, `.env`, build artifacts), `.editorconfig`, `.pre-commit-config.yaml`, `LICENSE`.
  - `backend/pyproject.toml` — uv-managed project, Python **3.12**; dev dependencies: `ruff`, `black`, `mypy`, `pytest`, `pytest-cov`. Configure `[tool.ruff]` (lint + isort), `[tool.black]`, `[tool.mypy]` (`strict = true`, `python_version = "3.12"`), `[tool.pytest.ini_options]` (`testpaths = ["tests"]`) and `[tool.coverage.report]` (`fail_under = 85`).
  - `backend/uv.lock` — committed lockfile (`uv lock`).
  - Create the package tree as empty packages with `__init__.py` so imports resolve later: `backend/app/`, `backend/app/{core,db,api,auth,authz,identity,groups,clinical,attachments,appointments,audit,modules,workers}/`, `backend/app/db/{models,repositories}/`, `backend/tests/`.
  - `frontend/package.json` — Vite + TypeScript + React 18; dev deps: `eslint`, `prettier`, `vitest`, `@vitejs/plugin-react`, `typescript`. Scripts: `dev`, `build`, `lint`, `format`, `test`, `typecheck` (`tsc --noEmit`).
  - `frontend/tsconfig.json` (`strict: true`), `frontend/.eslintrc.cjs`, `frontend/.prettierrc`, `frontend/vite.config.ts`, `frontend/vitest.config.ts`.
  - Frontend source tree as placeholders: `frontend/src/{app,api,auth,core,modules}/`, `frontend/tests/`.
  - `infra/` directory placeholder (compose + reverse-proxy land in TASK-004): keep `infra/.gitkeep`.
- Tooling specifics:
  - `pre-commit` hooks: `ruff` (lint + fix), `black`, `mypy` (backend paths), `eslint` + `prettier` (frontend paths), and a hook that blocks committing `.env` / secret files (NFR-007 — see TASK-003 for the full secret policy).
  - Pin tool versions in `pyproject.toml` / `package.json` and the pre-commit config so CI (TASK-005) runs identical versions.
- Config keys: none (config is TASK-003).
- Error cases: none (no runtime).

## Tests (write first — TDD, CLAUDE.md §4)

- Backend smoke test `backend/tests/test_toolchain.py`: imports the top-level `app` package and every sub-package created above, asserting the layout exists and is importable (guards against a broken skeleton).
- Frontend smoke test `frontend/tests/toolchain.test.ts`: a trivial Vitest assertion proving the test runner, TS transform, and config resolve.
- Tooling is verified by running, in a clean checkout: `uv sync && uv run ruff check && uv run mypy && uv run pytest` and `npm ci && npm run lint && npm run typecheck && npm test`. These commands form the executable acceptance check and are the same ones CI will run (TASK-005).

## Acceptance criteria

Distilled from NFR-006 (controlled lifecycle outputs under version control) and SR-028 (uniquely identified, version-controlled, traceable records):

- [ ] The repo layout matches the template exactly; all listed packages/directories exist and are committed.
- [ ] `uv sync` resolves from a committed `uv.lock`; backend uses Python 3.12.
- [ ] `ruff`, `black`, `mypy` (strict), `pytest` run from the backend with zero config errors.
- [ ] `eslint`, `prettier`, `tsc --noEmit`, `vitest` run from the frontend with zero config errors.
- [ ] `pre-commit run --all-files` passes and includes a hook that prevents committing `.env`/secret files.
- [ ] `README.md` documents the build/run quickstart (NFR-006 build/deploy instructions, version-controlled).
- [ ] Tool versions are pinned so CI and local runs are identical.

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy` and `eslint`/`tsc`)
- [ ] Unit tests pass; coverage gate (`fail_under = 85`) wired even if trivially met here
- [ ] OpenAPI regenerated and re-linted (N/A — no API)
- [ ] Audit events emitted for security-relevant actions (N/A — no runtime)
- [ ] Traceability matrix row updated (NFR-006, SR-028 → TASK-001 → toolchain tests)
- [ ] Security review completed (N/A — no auth/session code)
