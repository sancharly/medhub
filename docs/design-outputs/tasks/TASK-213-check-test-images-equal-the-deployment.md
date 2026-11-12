---
id: "TASK-213"
type: task
title: "CI check that test container images equal the deployment's"
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
  - target: "PRB-040"
    relation: relates_to
  - target: "ADD-024"
    relation: relates_to
  - target: "TS-013"
    relation: relates_to
  - target: "TASK-211"
    relation: relates_to
  - target: "TASK-212"
    relation: relates_to
tags: ["ci", "verification", "soup", "cr:CR-005", "control:protective"]
---

# TASK-213 — CI check that test container images equal the deployment's

- **Software item / unit:** SI-DEVINFRA `U-INF-CIPipeline` (ADD-024), `infra/check_image_pins.py`.
- **PRB:** PRB-040. **CR:** CR-005 (AC-6; negative control). **ADR:** ADR-0020 (Proposed).
- **Depends on:** TASK-211 (same script, test file and `--root` mechanism), TASK-212 (the
  definition it reads).
- **Branch:** `bug/build-hygiene`.
- **Size:** M (`infra/check_image_pins.py`, `infra/tests/test_check_image_pins.py`, fixture trees,
  TS-013, ADD-024, PRB-040).

## Objective

SR-028 AC-9, enforcement: CI fails, naming file and line, when a test's SOUP image reference
differs from the deployment definition or has no digest, so a later edit cannot bring a floating
tag back (PRB-040 grew from two call sites to eleven without one).

## Implementation detail

Per ADR-0020, three rules over the repository root:

1. `backend/tests/postgres_image.py`: exactly one `POSTGRES_IMAGE = "<ref>"` line; `<ref>` has a
   digest and equals the `image:` of the `postgres` service in `infra/docker-compose.yml`. A
   missing file, a missing or second assignment, or a missing Compose service is a finding.
2. Every workflow `services.<name>.image` must equal the Compose `image:` of the service with the
   same image repository (`postgres`, `redis` at HEAD; SR-028 AC-9 covers CI service containers,
   which are test containers of SOUP components). A service image with no Compose counterpart is
   a finding.
3. A string literal of the form `"<repo>:<tag…>"` or `'<repo>:<tag…>'`, where `<repo>` is the image
   repository of any Compose service and `<tag>` starts with an alphanumeric (so
   `"redis://localhost:6379/0"` does not match), in `backend/**/*.py` outside
   `backend/tests/postgres_image.py`, is a finding (`.venv/` excluded).

Messages, e.g. `backend/tests/postgres_image.py:N: test image differs from infra/docker-compose.yml:126: <ref>`.

## Tests (write first)

New class `TestImagesMatchDeployment` in `infra/tests/test_check_image_pins.py`, on fixture trees
(`--root`): definition equal (pass); tag differs; digest missing; digest differs; definition file
missing; two assignments; workflow service `postgres:16` against a pinned Compose image; a
`"postgres:16"` literal in another test file (fail); `"redis://localhost:6379/0"` (pass).

## Acceptance criteria

- [ ] CR-005 AC-6: each failing case is reported with file and line; the passing cases pass; the
      check passes on the repository.
- [ ] Negative control: on a scratch copy, setting `POSTGRES_IMAGE` to `postgres:16`, dropping its
      digest, or adding `PostgresContainer("postgres:16")` to one test each make the check exit 1.
- [ ] Records: TS-013 1.6 gains TC-013.13 (unit, test-image rules); ADD-024 1.3 describes the
      rules; PRB-040 `## Resolution` written (TASK-212, TASK-213).

## Verification

```sh
python3 -m unittest discover -s infra/tests -v
python3 infra/check_image_pins.py; echo "exit $?"   # 0
```

## Records

TS-013, ADD-024 (version rule in TASK-211). PRB-040 `resolved` only after QA approves (AC-11).

## Version history

- 1.0 (2026-11-12) — Created at the CR-005 Plan stage (Software Architect role); `draft`.
