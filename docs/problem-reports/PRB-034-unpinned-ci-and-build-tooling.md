---
id: "PRB-034"
type: problem-report
title: "CI and image-build tooling is referenced by floating versions"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
criticality: minor
links: []
tags: ["configuration-management", "reproducibility"]
---

# PRB-034 — CI and image-build tooling is referenced by floating versions

## Observed

The tools that build and verify MedHub are referenced by moving versions:

- `.github/workflows/ci.yml`: GitHub Actions by major tag (`actions/checkout@v4`,
  `actions/setup-python@v5`, `actions/setup-node@v4`), `python-version: "3.12"` and
  `node-version: "20"` without a patch version.
- `backend/Dockerfile`: `pip install uv` with no version.
- `.github/workflows/ci.yml`: `pip install uv` with no version in the backend-quality,
  backend-tests and openapi-lint jobs. Since CR-001 (TASK-158) the backend-quality job runs
  `uv lock --check`, so a uv release that changes the lock format would fail CI with no code change
  (fails safe, but can block merges).

## Impact

- **IEC 62304 §5.8.5 / §8.1**: two builds of the same commit can use different tool versions, so a
  release build is not strictly reproducible. None of these tools ships in the product, so they
  are not SOUP and do not affect the SOUP list.
- A silent change in `uv` resolution or in an action could alter what is installed or verified
  without a code change.

## Safety evaluation

No hazard is realized: the shipped dependencies are fixed by the committed lock files and, after
CR-001, by image digests. The effect is on build reproducibility evidence, not on runtime behaviour,
hence `minor`.

## Proposed resolution

Pin GitHub Actions by commit SHA (with the version in a comment), set full patch versions for
`python-version` and `node-version`, and install a pinned `uv` version in `backend/Dockerfile`.
Needs a task and a CR.

## Source

Raised during the Specify stage of CR-001 (2026-10-22), which leaves it out of scope.
