---
id: "TASK-156"
type: task
title: "CI check that rejects image references without a digest"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
links:
  - target: "SR-028"
    relation: implements
  - target: "RISK-010"
    relation: mitigates
  - target: "TASK-155"
    relation: relates_to
tags: ["soup", "configuration-management", "regulatory", "cr:CR-001", "issue:sancharly/medhub#26", "control:protective"]
---

# TASK-156 — CI check that rejects image references without a digest

- **Software item / unit:** SI-DEVINFRA, `U-INF-CIPipeline` (ADD-024)
- **Depends on:** TASK-155 (the repository must be pinned, or the new job fails on `main`), as a
  `relates_to` link
- **Branch:** `bug/soup-pinning`

## Objective

Keep PRB-001 from coming back. A CI job fails, naming file and line, whenever a Compose `image:`,
Dockerfile `FROM` or workflow `services.*.image` reference has no `@sha256:` digest (SR-028 AC-5,
CR-001 AC-3, D-1). This is the protective control CR-001 adds to RISK-010. It closes PRB-001
together with TASK-155.

## Interfaces to honor

- **CLI:** `python3 infra/check_image_pins.py [PATH ...]`
  - No arguments: scan the tracked files from `git ls-files` that match `**/docker-compose*.yml`,
    `**/compose*.yml`, `**/Dockerfile`, `**/Dockerfile.*`, `.github/workflows/*.yml` and
    `.github/workflows/*.yaml`, excluding `infra/tests/fixtures/`.
  - Arguments: scan exactly those files (used by the tests).
  - Output per finding: `<path>:<line>: image reference without @sha256 digest: <ref>`. Exit `1`
    if any finding, `0` otherwise, `2` on a usage or read error.
- Python 3 standard library only, so the job needs no dependency install and no `setup-python`
  (the runner's `python3`). No YAML parser: line-based matching is enough for the forms used here
  and keeps the check free of SOUP.
- Must **not** flag: a `FROM` naming an earlier stage of the same Dockerfile (`FROM build`), or
  `FROM scratch`. `FROM --platform=… <ref>` and `FROM <ref> AS <name>` are parsed. A `FROM` or
  `image:` whose reference contains a variable (`$`, `${…}`) is flagged, because it cannot be
  verified statically.

## Implementation detail

- `infra/check_image_pins.py`:
  - Compose and workflow files: every `image:` value (quotes stripped, trailing comment ignored).
    In workflow files this covers `services.*.image` and any `container.image`.
  - Dockerfiles: `FROM` instructions (case-insensitive); collect stage names from `AS <name>` as
    the file is read, so a later `FROM <name>` is skipped.
  - A reference is pinned when it matches `@sha256:[0-9a-f]{64}$`.
- `infra/tests/test_check_image_pins.py` (`unittest`), fixtures in `infra/tests/fixtures/`:
  - unpinned Compose `image:` → exit 1, finding names file and line
  - unpinned Dockerfile `FROM`, including with `--platform` and `AS` → exit 1
  - unpinned workflow `services.*.image` → exit 1
  - `FROM <earlier stage>` and `FROM scratch` → not flagged
  - a reference with a short or uppercase digest → flagged
  - fully pinned fixtures → exit 0
- `.github/workflows/ci.yml`: new job `image-pins` (name "Image Pin Check"), `runs-on:
  ubuntu-latest`, no `needs`. Steps: `actions/checkout@v4` (same tag as the other jobs; PRB-034),
  `python3 -m unittest discover -s infra/tests -v`, `python3 infra/check_image_pins.py`. The
  workflow already triggers on every push and on pull requests to `main`.
- **ADD-024** (approved, so: `version` 1.1, approval record removed, `in_review` at handoff,
  version-history entry citing CR-001):
  - `U-INF-CIPipeline`: add the image pin check job and the script it runs (SR-028 AC-5).
  - Interfaces: "PostgreSQL 16 as a CI service container" becomes "PostgreSQL and Redis service
    containers at the Compose-pinned references".
  - Verification: add the TS-013 cases below.
  - TASK-157 and TASK-158 add the production-dependency-set step of the Docker Build job under
    the same `1.1`.
- **TS-013** (approved, so: `version` 1.2, approval record removed, `in_review` at handoff;
  TASK-157/158/159 add their cases under the same `1.2`):
  - `TC-013.5` | SR-028 | `infra/check_image_pins.py` (CI job `image-pins`) on the repository |
    every image reference carries a digest | exit 0
  - `TC-013.6` | SR-028 | `infra/tests/test_check_image_pins.py` | each unpinned fixture form is
    reported with file and line; stage and `scratch` references are not | exit 1 on each unpinned
    fixture, 0 on the pinned one; all unit tests pass
  - Update "Preconditions and environment": branch `bug/soup-pinning`; the pinned image references
    are those in the SOUP records.
- **PRB-001** → `status: resolved`, `version` 1.1, `updated` bumped. Add `## Resolution` naming the
  changed files of TASK-155 and this task and the reproducible verification (TC-013.5, TC-013.6,
  the AC-5 smoke run). The `resolves` link already exists on CR-001.

## Tests (write first)

Write `infra/tests/test_check_image_pins.py` and its fixtures first; it fails until the script
exists. Then implement the script until the suite passes and the repository scan exits 0.

## Acceptance criteria

- [ ] CR-001 **AC-3**: the job runs on every pull request; it fails, naming file and line, on any
      unpinned Compose, Dockerfile or workflow service reference; it ignores stage and `scratch`
      references; it passes on the repository. Negative evidence: the fixture tests, plus one
      temporary unpinned edit showing a non-zero exit (record the output in the handoff).
- [ ] CR-001 **AC-17** (PRB-001 part): PRB-001 `resolved` with its `## Resolution`.
- [ ] CR-001 **AC-15** (pin-check part): TC-013.5 and TC-013.6 in TS-013.

## Verification

```sh
python3 -m unittest discover -s infra/tests -v
python3 infra/check_image_pins.py                  # expect exit 0
sed -i.bak 's/@sha256:[0-9a-f]*//' infra/docker-compose.yml && python3 infra/check_image_pins.py; echo "exit=$?"
mv infra/docker-compose.yml.bak infra/docker-compose.yml   # expect exit=1 above, with file:line
python3 infra/check_image_pins.py; echo "exit=$?"            # expect exit=0 again
```

After push: the `image-pins` job is green on the branch head.

## Definition of Done

- [ ] Unit tests and repository scan pass locally and in CI
- [ ] ADD-024, TS-013 and PRB-001 updated; ADD-024 and TS-013 `in_review`
- [ ] `traceability-check` shows no error for the touched records
