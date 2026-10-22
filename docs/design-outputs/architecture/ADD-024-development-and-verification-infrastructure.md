---
id: ADD-024
type: architecture-doc
title: Development and verification infrastructure (SI-DEVINFRA)
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
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
  (SR-028 AC-5, CR-001 AC-3). The `build` job ("Docker Build") builds the backend image, which
  installs with `uv sync --frozen --no-dev`, and then runs the step "Check production dependency
  set": `docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.util, sys; import boto3; sys.exit(importlib.util.find_spec('fakeredis') is not None)"`.
  It fails the build when the production dependency set lacks the object-storage SDK or contains
  `fakeredis`, which only the tests use (SR-028 AC-5, CR-001 AC-8, AC-9). The `backend-quality`
  job runs `uv lock --check` before it installs, so a manifest edit that is not re-locked fails
  the pull request (SR-028 AC-5).
- `U-INF-Toolchain` — the monorepo toolchain configuration: `backend/pyproject.toml` tool sections,
  `.pre-commit-config.yaml`, the frontend ESLint and TypeScript configuration, and the lock files
  that pin every dependency (SR-028 AC-1).
- `U-INF-ContractExport` — `backend/app/export_openapi.py` and `npm run generate:types`: the
  committed OpenAPI schema and the generated frontend types, kept identical to the implementation
  by the `openapi-lint` job (the contract rule in `CLAUDE.md`).

Built by TASK-001 (monorepo and tooling) and TASK-005 (CI pipeline).

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
`infra/tests/test_check_image_pins.py` (TC-013.5, TC-013.6), `uv lock --check` (the `backend-quality`
step "Check the lock file is current") and the Docker Build step "Check production dependency set"
(TC-013.7, TC-013.8), plus the `traceability-check` gap
reports.

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
