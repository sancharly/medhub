---
id: ADD-024
type: architecture-doc
title: Development and verification infrastructure (SI-DEVINFRA)
status: approved
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-11-13"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-13"
approved_digest: 3233f449d279189014e95957b261106d6665638728cc6f3d503e9d26bdeadaf0
approval_note: self-approved
links:
  - target: SR-028
    relation: implements
tags:
  - software-item:SI-DEVINFRA
  - class:B
  - layer:tooling
---

# ADD-024 — Development and verification infrastructure (SI-DEVINFRA)

## Responsibility

The software that keeps every change identified, version-controlled, verified and traceable before
it can reach `main` (SR-028). It is part of the repository and runs on every pull request, but it is
**not deployed**: no runtime item depends on it, and it handles no PHI.

## Software units (IEC 62304 §5.4.1)

- `U-INF-CIPipeline` — `.github/workflows/ci.yml`: backend quality (ruff, black, mypy), backend
  tests against real PostgreSQL and Redis service containers with migrations applied, frontend
  quality (ESLint, tsc), frontend tests, the OpenAPI lint gate and the image pin check. A failing job
  blocks the merge (SR-028 AC-4). The `image-pins` job ("Image Pin Check") runs the unit tests of
  `infra/check_image_pins.py` and then the script on the repository. The script (Python standard
  library only, no dependency install) fails, naming file and line, when a Compose `image:`,
  Dockerfile `FROM` or `.github/workflows/*.yml` `services.*.image`, `container.image` or
  `container: <ref>` reference lacks `@sha256:<64 hex>` (an empty `image:` value also fails); it ignores a `FROM` of an earlier stage and `FROM scratch`
  (SR-028 AC-5, CR-001 AC-3). The same script, run without arguments, also applies the tool rules
  of SR-028 AC-8 to the tracked workflows and Dockerfiles (CR-005, ADR-0020) and fails, naming file
  and line, on: a repository action `uses:` that is not `owner/repo@<40 hex>` followed by a
  `# v<tag>` comment (`./` is exempt; `docker://` is checked by the image rule, which reports it
  without `@sha256:<64 hex>`; `astral-sh/setup-uv` is reported); a `python-version` or `node-version` that is
  not `X.Y.Z` (a `*-version-file` key is reported) or differs from the tag version of `FROM python:` in `backend/Dockerfile` or
  `FROM node:` in `frontend/Dockerfile` (the shipped references are the source of truth); a `uv`
  `pip` / `pipx` install that is not `uv==X.Y.Z` (`\`-continued lines and the Dockerfile exec form are read), or whose version
  differs from the one in `backend/Dockerfile`; and an `npx` package without an exact version. A
  form of these kinds that it cannot parse is a finding. A stray trailing `\` does not join a
  workflow line into the next YAML key, list item or blank line, and a Dockerfile continuation skips
  comment lines, as Docker does. Matching is line-based, so these are not seen: an `npx` or a
  `pip install uv` reached through a script file, a `uses:` or `run:` assembled by a YAML anchor or
  template expression, and composite actions under `.github/actions/`; for the test images, a job
  `container:` or `uses: docker://` image (checked by the image rule only: a digest is present, not
  equality with Compose), a container class other than `PostgresContainer` (the one that occurs is
  the `DockerContainer` Redis call in `backend/tests/auth/test_session_cap_concurrency.py`, which
  reads the Compose image at run time), a `PostgresContainer` reached under another name without
  `import ... as` (`PC = PostgresContainer`, `getattr`, `import *`), a `POSTGRES_IMAGE` rebound
  through `setattr(...)`, `sys.modules` or `vars()` in a file other than the definition file (inside it,
  a `globals()`, `locals()`, `vars()` or `setattr()` call is a finding), and an import of
  `POSTGRES_IMAGE` from a module other than `backend/postgres_image.py`; none of the others occurs
  in the repository.
  Four test image rules (SR-028 AC-9, CR-005 AC-6, ADR-0020) run with the tool rules, over the
  tracked files or those under `--root`: (1) `backend/postgres_image.py` holds exactly one
  `POSTGRES_IMAGE` assignment at the start of a line, as `POSTGRES_IMAGE = "<ref>"` or as
  `POSTGRES_IMAGE = (`, one string literal and `)` (concatenation, an f-string, a name, a missing
  `)`, an annotation or anything else on those lines is a finding; every later binding of the
  name, read with `ast` (plain, annotated, augmented, tuple unpacking, `:=`, `for`, `with ... as`,
  `import ... as`, `import POSTGRES_IMAGE` / `from x import POSTGRES_IMAGE`, `global`, `except ... as`, a
  `def` / `async def` / `class` of that name, a `match` capture, a `;`-joined statement, or a `globals()` /
  `locals()` / `vars()` / `setattr()` call), is a
  second assignment, and a definition file that does not parse is a finding), and `<ref>` carries a digest and
  equals the `image:` of the `postgres` service in `infra/docker-compose.yml`; (2) every workflow
  `services.<name>.image` equals the Compose `image:` of the service with the same image
  repository (`postgres`, `redis`), and one with no Compose counterpart is a finding, as is a
  service written as an inline mapping (`postgres: {image: …}`, not read); (3) a string literal
  `"[registry/namespace/]<repo>:<tag>"` of a Compose image repository in `backend/**/*.py`
  (`.venv/` excluded) is a finding, in `backend/postgres_image.py` too apart from the one
  recognised `POSTGRES_IMAGE` literal; connection URLs such as `redis://localhost:6379/0` do not
  match, but a `host:port` or log string such as `"postgres:5432"` or `"redis:connected"` does (a
  false positive that fails closed: rewrite the literal, do not weaken the rule); (4) every
  `PostgresContainer(` call in `backend/**/*.py` passes `POSTGRES_IMAGE` as its first positional
  argument or as `image=POSTGRES_IMAGE` (no argument, a literal or another name is a finding),
  so a `PostgresContainer` call site cannot bring a floating tag back; a `PostgresContainer` imported
  under an alias (`import ... as`) and a `POSTGRES_IMAGE` binding in a `backend/**/*.py` file other
  than the definition (assignment, `import ... as`, attribute store) are findings too. `--root ""` exits 2.
  The pins it enforces are: actions `actions/checkout`, `actions/setup-python` and
  `actions/setup-node` by commit SHA with the release tag in a comment, CI Python 3.12.15 and
  Node.js 24.22.2 (the base-image versions), `uv==0.13.7` in `backend/Dockerfile` and the four CI
  jobs that install it, and `@redocly/cli@2.77.0`. The hosted runner image (`runs-on: ubuntu-latest`,
  with its Docker, Compose, system `pip` and `openssl`) is not pinned by any repository reference; it
  is a documented limit of SR-028 AC-8 (CR-005 Q-6): no released image is built on it and every tool
  the repository installs on it is pinned. The `build` job ("Docker Build") builds the backend image, which
  installs with `uv sync --frozen --no-dev`, and then runs the step "Check production dependency
  set": `docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.util, sys; import boto3; sys.exit(importlib.util.find_spec('fakeredis') is not None)"`.
  It fails the build when the production dependency set lacks the object-storage SDK or contains
  `fakeredis`, which only the tests use (SR-028 AC-5, CR-001 AC-8, AC-9). The `backend-quality`
  job runs `uv lock --check` before it installs, so a manifest edit that is not re-locked fails
  the pull request (SR-028 AC-5). The `object-store-integration` job ("Object Store Integration",
  CR-002 AC-7, SR-022 AC 5) starts the real object store with the Compose project `medhub-ci`,
  `infra/docker-compose.yml` and the CI-only override `infra/compose.ci-object-store.yml`, then
  runs the pytest marker `object_store` (`backend/tests/integration/test_object_store_sse.py`)
  against it. The reason for the override is in
  [07 deployment view](../../design/07-deployment-view.md); the store itself is ADD-025.
- `U-INF-Toolchain` — the monorepo toolchain configuration: `backend/pyproject.toml` tool sections,
  `.pre-commit-config.yaml`, the frontend ESLint and TypeScript configuration, and the lock files
  that pin every dependency (SR-028 AC-1).
- `U-INF-ContractExport` — `backend/app/export_openapi.py` and `npm run generate:types`: the
  committed OpenAPI schema and the generated frontend types, kept identical to the implementation
  by the `openapi-lint` job (the contract rule in `CLAUDE.md`).

Built by TASK-001 (monorepo and tooling), TASK-005 (CI pipeline) and, for the
`object-store-integration` job and its override file, TASK-179.

## Requirements implemented

Software requirements: SR-028. Non-functional requirements constraining this item: NFR-005, NFR-006.

The parts of SR-028 that are process rather than software — record IDs, statuses, links and
approvals — are defined by the lifecycle plans ([PLAN-001](../../plans/PLAN-001-software-development-plan.md),
[PLAN-003](../../plans/PLAN-003-configuration-management-plan.md)) and checked by
`traceability-check`; this record covers the software that enforces them.

## Interfaces

- Consumes: the repository contents and the GitHub Actions runner; PostgreSQL and Redis service
  containers at the Compose-pinned references (tag and digest).
- Provides: pass/fail status checks on pull requests, the committed `backend/openapi/openapi.json`
  and `frontend/src/api/generated/openapi.ts`.

## Verification

[TS-013](../tests-specifications/TS-013-lifecycle-record-and-traceability.md):
`backend/tests/test_toolchain.py`, `frontend/tests/toolchain.test.ts` and
`backend/tests/test_export_openapi.py`, `infra/check_image_pins.py` with
`infra/tests/test_check_image_pins.py` (TC-013.5, TC-013.6, TC-013.11; TC-013.12 for the pins in the repository and on hosted CI), `uv lock --check` (the `backend-quality`
step "Check the lock file is current") and the Docker Build step "Check production dependency set"
(TC-013.7, TC-013.8), plus the `traceability-check` gap
reports. [TS-008](../tests-specifications/TS-008-persistence-fhir-aligned-model-and-encryption.md) lists TC-008.8, the
`object-store-integration` job, and the override check in `infra/tests/test_compose_object_store.py`.

## Architecture narrative

Described in [05 building blocks](../../design/05-building-blocks.md), section
"Development and verification infrastructure", and in the configuration management plan
(PLAN-003). Governing decisions: [ADR-0011](../../design/adr/) (process controls).

## Risk relevance

Supports the controls of RISK-007 and RISK-010 through SR-028; it is not itself a hazard
contributor because it is not deployed.

## Version history

- 1.0 (2026-10-21) — Initial record.
- 1.1 (2026-10-22) — CR-001: `U-INF-CIPipeline` gains the image pin check job and its script
  (`infra/check_image_pins.py`, SR-028 AC-5); CI service containers are the Compose-pinned PostgreSQL
  and Redis references; verification lists TC-013.5 and TC-013.6. TASK-157 adds the step "Check
  production dependency set" to the Docker Build job (`import boto3` in the built backend image,
  TC-013.8) and lists TC-013.7. TASK-158 extends the same step with the absence of `fakeredis`
  (PRB-033, CR-001 AC-9) and adds the `backend-quality` step "Check the lock file is current"
  (`uv lock --check`, TC-013.7).
- 1.2 (2026-10-30) — CR-002 TASK-180: `U-INF-CIPipeline` gains the job `object-store-integration`
  and the CI-only override `infra/compose.ci-object-store.yml` (TASK-179); verification lists
  TC-008.8. Status returned to `in_review` and the approval record cleared for re-approval by the
  human.
- 1.3 (2026-11-12) — CR-005 TASK-211: `U-INF-CIPipeline` describes the tool rules of the pin check
  (actions by SHA, CI runtimes equal to the base images, one exact `uv`, exact `npx` packages), the
  pins it enforces and the unpinned hosted runner image as a documented limit; verification lists
  TC-013.11 and TC-013.12. Status returned to `in_review` and the approval record cleared for
  re-approval by the human. TASK-213 added the test-image rules (and the three fixes to the line
  joining and the `--root` check) to this version, without a version change.
  TASK-216 (TASK-213 QA round 2, LOW 1-3): rule 1 reads the definition file with `ast`, rule 4 also reports a
  `PostgresContainer` import under an alias and a `POSTGRES_IMAGE` binding outside the definition, and the
  "not seen" list names the `DockerContainer` Redis call and the forms still not seen; version unchanged.
  TASK-216 (QA L-1): rule 1 also reports `def` / `async def` / `class` of the name, `match` captures,
  `import POSTGRES_IMAGE` and `from x import POSTGRES_IMAGE` without `as`, and a `setattr()` call in the
  definition file, and a function parameter named `POSTGRES_IMAGE` in a test file; the "not seen" list
  now says `setattr` is seen inside the definition file only.
