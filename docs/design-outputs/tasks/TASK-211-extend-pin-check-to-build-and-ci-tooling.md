---
id: "TASK-211"
type: task
title: "Extend the pin check to build and CI tool references"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-12"
updated: "2026-11-12"
links:
  - target: "SR-028"
    relation: implements
  - target: "RISK-010"
    relation: mitigates
  - target: "CR-005"
    relation: relates_to
  - target: "PRB-034"
    relation: relates_to
  - target: "ADD-024"
    relation: relates_to
  - target: "TS-013"
    relation: relates_to
  - target: "TASK-209"
    relation: relates_to
  - target: "TASK-210"
    relation: relates_to
tags: ["ci", "reproducibility", "verification", "cr:CR-005", "control:protective"]
---

# TASK-211 — Extend the pin check to build and CI tool references

- **Software item / unit:** SI-DEVINFRA `U-INF-CIPipeline` (ADD-024), `infra/check_image_pins.py`.
- **PRB:** PRB-034. **CR:** CR-005 (AC-4; negative control). **ADR:** ADR-0020 (Proposed).
- **Depends on:** TASK-209, TASK-210 (the repository must pass the new rules). Ordered before
  TASK-213 (same script and test file).
- **Branch:** `bug/build-hygiene`.
- **Size:** M (`infra/check_image_pins.py`, `infra/tests/test_check_image_pins.py`, new fixtures
  under `infra/tests/fixtures/`, TS-013, ADD-024, PRB-034).

## Objective

SR-028 AC-8, enforcement: CI fails, naming file and line, on an action without a 40-hex SHA, a
`python-version` or `node-version` without a patch version or different from its base image, a
`uv` install without an exact version or with a version that differs from another, and an `npx`
package without an exact version. The existing image rule and its output are unchanged.

## Implementation detail

Per ADR-0020, in `infra/check_image_pins.py` (standard library only, line-based):

1. Workflow `uses:`: a repository action must be `owner/repo[/path]@<40 hex>` followed by
   `# v<tag>`; `./…` is exempt; `docker://…` goes to the existing image rule.
2. Workflow `python-version:` / `node-version:`: value `X.Y.Z`, equal to the tag version of
   `FROM python:X.Y.Z-…` in `backend/Dockerfile` / `FROM node:X.Y.Z-…` in `frontend/Dockerfile`.
   An expression (`${{ … }}`) or a list is a finding.
3. `uv` installs in workflow `run:` lines and Dockerfile `RUN` lines (`pip install uv`, `pip
   install "uv…"`, `pipx install uv`): must be `uv==X.Y.Z`; all versions in the repository equal.
4. Workflow `npx`: the first non-option argument must be `name@X.Y.Z` (scoped names included).
5. Cross-file rules run over a repository root: default the git repository (tracked files,
   `infra/tests/fixtures/` excluded); a `--root DIR` option points them at a fixture tree. The
   positional-path mode for images stays as it is.
6. Message per rule, e.g. `<path>:<line>: action not pinned to a commit SHA: actions/checkout@v4`,
   `... python-version differs from backend/Dockerfile (3.12.15): 3.12`. Exit codes unchanged
   (0 / 1 / 2).
7. The module docstring and `--help` text list every rule. The CI job "Image Pin Check" is not
   renamed (TASK-208 and TS-013 refer to it).

## Tests (write first)

`infra/tests/test_check_image_pins.py`, new classes (subprocess runs, as the existing ones):

- `ToolReferences`: one failing and one passing fixture per form: `uses:` by tag, by short SHA,
  by SHA without the tag comment; `python-version: "3.12"`, `"3.12.16"` (patch differs from the
  base image), an expression; `node-version: "24"`; `pip install uv`, `pip install "uv>=0.13"`,
  two different `uv==` versions; `npx --yes @redocly/cli`; `uses: ./local-action` passes.
- Each finding asserts the fixture file and line.
- The existing 11 tests are unchanged and pass.

## Acceptance criteria

- [ ] CR-005 AC-4: each form above fails with file and line; each pinned form passes; the check
      passes on the repository (exit 0).
- [ ] Negative control: reverting one action to `@v4`, one `python-version` to `"3.12"`, one uv
      install to `pip install uv` and the linter to `@redocly/cli` each makes
      `python3 infra/check_image_pins.py` exit 1 with the right file and line (scratch copy).
- [ ] Records: TS-013 gains TC-013.11 (unit, tool rules) and TC-013.12 (integration/review:
      repository run exit 0; SHA-to-tag record of TASK-209; `uv lock --check` with the pinned uv;
      hosted logs show 3.12.15, 24.22.2, uv 0.13.7); ADD-024 `U-INF-CIPipeline` describes the
      extended check and the pinned tools; PRB-034 `## Resolution` written (TASK-209..211).

## Verification

```sh
python3 -m unittest discover -s infra/tests -v
python3 infra/check_image_pins.py; echo "exit $?"      # 0
# negative control on a scratch copy of the repository, one mutation at a time
```

## Records

- **TS-013** (`approved` 1.5): the first CR-005 task that changes it bumps it to 1.6, clears the
  approval record and sets `in_review`; later CR-005 tasks add to 1.6 (CR-002 rule).
- **ADD-024** (`approved` 1.2): same rule, 1.3.
- **PRB-034**: `## Resolution` names TASK-209, 210, 211 and their commits; `resolved` only after
  QA approves this task (AC-11).

## Version history

- 1.0 (2026-11-12) — Created at the CR-005 Plan stage (Software Architect role); `draft`.
