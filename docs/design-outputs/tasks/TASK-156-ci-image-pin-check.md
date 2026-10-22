---
id: "TASK-156"
type: task
title: "CI check that rejects image references without a digest"
status: approved
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
    In workflow files this covers `services.*.image`, `container.image` and the shorthand `container: <ref>`; an empty `image:` value is reported.
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

- [x] CR-001 **AC-3**: the job runs on every pull request; it fails, naming file and line, on any
      unpinned Compose, Dockerfile or workflow service reference; it ignores stage and `scratch`
      references; it passes on the repository. Negative evidence: the fixture tests, plus one
      temporary unpinned edit showing a non-zero exit (record the output in the handoff).
- [x] CR-001 **AC-17** (PRB-001 part): PRB-001 `resolved` with its `## Resolution`.
- [x] CR-001 **AC-15** (pin-check part): TC-013.5 and TC-013.6 in TS-013.

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
- [x] ADD-024, TS-013 and PRB-001 updated; ADD-024 and TS-013 `in_review`
- [x] `traceability-check` shows no error for the touched records

## Implementation notes and evidence

Handed to QA on 2026-10-22 (status `in_review`). Checkboxes are left for QA.

**Files.** New: `infra/check_image_pins.py`, `infra/tests/test_check_image_pins.py`, nine fixtures in
`infra/tests/fixtures/` (`compose_unpinned.yml`, `compose_pinned.yml`, `Dockerfile.unpinned`,
`Dockerfile.stages`, `Dockerfile.pinned`, `Dockerfile.badpin`, `Dockerfile.variable`,
`workflow_unpinned.yml`, `workflow_pinned.yml`). Changed: `.github/workflows/ci.yml` (job
`image-pins`, "Image Pin Check", no `needs`, `actions/checkout@v4`, then the unit tests, then the
script), ADD-024 (1.1, `in_review`), TS-013 (1.2, `in_review`, TC-013.5 and TC-013.6), PRB-001
(`resolved`, 1.1, `## Investigation` and `## Resolution`).

**Design points.**
- Without arguments the script scans `git ls-files` matches, run from the repository root whatever
  the working directory. Today that is `.github/workflows/ci.yml`, `backend/Dockerfile`,
  `frontend/Dockerfile` and `infra/docker-compose.yml`. No tracked file at all is an error (exit 2),
  so the check cannot pass on an empty scan.
- Beyond the task text: Compose patterns also match `.yaml`, for symmetry with the workflow
  patterns, and a `-` list prefix before `image:` is accepted. Stage names are matched
  case-insensitively, as Docker does. Nothing else is added.
- A reference containing `$` is flagged in all three file kinds, even when the digest is present,
  because it cannot be verified statically. `FROM --platform=$BUILDPLATFORM <pinned>` is not flagged
  (only the reference is checked).
- Known limits of line-based matching (not needed here, not handled): `FROM` continued over several
  lines (only the first line is read), and a flow mapping such as `image: {…}` (flagged as
  written, not parsed). `ARG`-fed `FROM` is flagged as a variable. The pins are also not checked to be unique per SOUP item (AC-2 stays an
  inspection).

**Verification run (2026-10-22, macOS, Python 3 from the system, branch `bug/soup-pinning`).**

| Command | Result |
|---|---|
| Fixture tests written first, before the script existed | 9 of 9 failed |
| `python3 -m unittest discover -s infra/tests -v` | `Ran 9 tests ... OK` |
| `python3 infra/check_image_pins.py` | no output, `exit=0` |
| Same, run from `/tmp` | `exit=0` (paths do not depend on the working directory) |
| Temporary edit: `sed -i.bak 's/@sha256:[0-9a-f]*//' infra/docker-compose.yml` then the script | `exit=1`, five findings (below); the edit was reverted with `mv`, and the script then gave `exit=0` again |
| Script on a nonexistent file | `error: cannot read /nonexistent: ...`, `exit=2` |
| `cd backend && uv run pytest -q` | `495 passed` |
| `cd frontend && npm test -- --run` | `27 passed` files, `155 passed` tests |
| Workflow YAML parsed with PyYAML (`uv run python`) | parses; jobs: backend-quality, backend-tests, frontend-quality, frontend-tests, openapi-lint, build, image-pins |

Output of the temporary-edit run:

```
infra/docker-compose.yml:20: image reference without @sha256 digest: nginx:1.31.8-alpine
infra/docker-compose.yml:69: image reference without @sha256 digest: postgres:16.15
infra/docker-compose.yml:84: image reference without @sha256 digest: redis:7.4.11-alpine
infra/docker-compose.yml:96: image reference without @sha256 digest: minio/minio:RELEASE.2025-09-07T16-13-09Z
infra/docker-compose.yml:114: image reference without @sha256 digest: minio/mc:RELEASE.2025-08-13T08-35-41Z
exit=1
```

**Not verified here.** GitHub Actions cannot be run locally: the `image-pins` job has not run in CI
and is checked only for YAML validity. The "job green on the branch head" check happens after the
push. `traceability-check` was not run by the developer role; QA runs it.

**Related defect outside this task:** PRB-040 (database tests start `postgres:16`) is a floating
reference in Python test code that this check does not scan. It is already recorded; no new PRB.

## QA review (2026-10-22)

**Verdict: APPROVED** (`in_review → approved`). ADD-024 stays `in_review` for the human. TS-013
also stays `in_review`, for three reasons. TASK-157..159 still add cases to it under the same 1.2.
CR-001 AC-18 requires every record changed by the CR to be `in_review`. And its Scope needs the
MEDIUM fix below. The Definition of Done item "in CI" stays open until the `image-pins` job is
green on the branch head (AC-16, Checkpoint A).

### Findings

- **[MEDIUM] PRB-001 safety evaluation is out of date.** At
  `docs/problem-reports/PRB-001-floating-container-image-tags.md:59-62` it still reads "Assessed
  with the RISK records once the register exists". The register exists: RISK-010 cites PRB-001 in
  its control table. The section also never says whether a released version in use is affected, so
  it is silent on notification (§9.3). → Name RISK-010 and SR-028 AC-5 as the assessment and its
  control. State that no `release` record exists (`docs/releases/` is absent), so no released
  version in use is affected and no notification is needed.
- **[MEDIUM] TS-013 Scope and Notes no longer describe the record.**
  `docs/design-outputs/tests-specifications/TS-013-lifecycle-record-and-traceability.md:24` says
  "the design record set (no code under test)", and line 55 says the TS verifies "by review". Both
  are wrong now that TC-013.5 and TC-013.6 test `infra/check_image_pins.py`. The class B unit
  acceptance criteria (lines 48-51) have no criterion for the script. → Add SI-DEVINFRA
  `U-INF-CIPipeline` (`infra/check_image_pins.py`) as a software item under test. Add a unit
  acceptance criterion, for example "every negative fixture exits 1 and names file and line; the
  pinned and stage fixtures exit 0". Reword the note to "by review (TC-013.1..4) and by unit tests
  (TC-013.5..6)". Make the fix before TASK-157 extends the 1.2 entry.
- **[LOW] Some line-based forms are missed, and the check passes them (fail-open).** Probed with
  ad-hoc files. Three YAML forms are not seen: `image:` with its value on the next line, the flow
  mapping `svc: {image: postgres:16}`, and a quoted key `"image": postgres:16`. The workflow
  shorthand `container: python:3.12` is not checked either, so the claim "any `container.image`"
  (line 55 above, and PRB-001:77) holds only for the mapping form. None of these forms occurs in
  the repository. AC-3 covers `services.*.image`, which is handled, so this does not block. → In
  `infra/check_image_pins.py` `image_values()`, report an empty `image:` value as a finding (fail
  closed), and in workflow files also match `^\s*container:\s*\S`. Or list these limits in ADD-024
  and TS-013 next to the ones already in the task notes.
- **[LOW] A digest-only reference passes.** `FROM postgres@sha256:<64 hex>` and
  `image: postgres@sha256:<64 hex>` exit 0. AC-3, and the CI sentence of SR-028 AC-5, ask only for
  the digest, so the check meets the criterion as written. The release-tag half of AC-1 remains an
  inspection. → Optional: require `:<tag>@sha256:` in `PINNED`. Otherwise add a sentence to
  TC-013.5 saying the check enforces the digest only.

Observations (no action): a `FROM` line continuation, a block scalar (`image: >-`), a YAML anchor
and `FROM --platform linux/amd64 <ref>` (no `=`) are all flagged, so they fail closed. The finding
text for the `--platform` form names `linux/amd64` as the reference. `pull_request` fires only for
PRs into `main`, but `push` on `**` runs the job on every PR branch of this repository, so AC-3's
"every pull request" holds. This trigger setup is the existing project convention. `uses:
docker://…` step images are outside AC-3 (PRB-034 covers CI tooling).

### Verification run (QA, 2026-10-22, Python 3.12.3)

| Command | Result |
|---|---|
| `python3 -m unittest discover -s infra/tests -v` | `Ran 9 tests ... OK` |
| `python3 infra/check_image_pins.py` (repo root, and from `/private/tmp`) | no output, exit 0 both times |
| Temporary edit: `sed -i.bak 's/@sha256:[0-9a-f]*//' backend/Dockerfile`, then the script | exit 1: `backend/Dockerfile:1` and `:9`, `python:3.12.15-slim`. Reverted with `mv`, `cmp` identical to the saved copy, `git status --short backend/Dockerfile` empty, script exit 0 again |
| Script on a digest-stripped copy of `.github/workflows/ci.yml` | exit 1: `:47 postgres:16.15`, `:60 redis:7.4.11-alpine` (`services.*.image`, D-1) |
| Edge-case probes (Dockerfile, Compose and workflow files in the scratchpad) | `As`/`BUILD` casing handled; `FROM build:1.0` flagged; the fail-open forms are listed under LOW above |
| Workflow parsed with PyYAML | `image-pins` job valid. Triggers: `push` on `**`, `pull_request` on `main`. Checkout, unit tests, then the script. No new dependency |
| `traceability-check` (fallback parser) on TASK-156, ADD-024, TS-013, PRB-001, CR-001, links resolved against all 329 records | 0 errors. One warning: `risk_control_unverified`, TASK-156 → RISK-010, no TR yet (expected until the release TR). E8 holds for ADD-024 and TS-013 (`implements`/`verifies` SR-028). E9 holds for PRB-001 (CR-001 `resolves`) |
| `cd backend && uv run pytest -q` | `495 passed` |
| `cd frontend && npm test -- --run` | 27 files, `155 passed` |

Pending, not blocking: the `image-pins` job's first CI run on the branch head (AC-16, Checkpoint A).

**Post-review confirmation (QA, 2026-10-22).** Status stays `approved`. Three findings are
resolved: both MEDIUM and the digest-only LOW. The fail-open LOW is partly resolved. QA re-ran
`unittest` (11 tests, OK), the repository scan (exit 0) and the scoped trace.py (0 errors).
Probes: an empty `image:` and `container: <ref>` each exit 1, and the `container:` mapping is not
flagged. Two forms still pass unreported and are documented nowhere: `svc: {image: x}` and a
quoted `"image": x`. The TS-013 unit criterion "exits 0 only when every … reference" therefore
claims more than the script checks. This is LOW and does not block. Fix it with one sentence on
the limit in TS-013 or ADD-024, or by matching `(^|[{,\s])["']?(image|container)["']?:`.

## Post-review fixes (developer, 2026-10-22)

Status left as set by QA. Fixes for the QA findings, same branch, nothing committed:

1. **[MEDIUM] PRB-001 Safety evaluation.** Rewritten: cites RISK-010 (its control table names this
   PRB's resolution) and SR-028 AC-5, and states that no `release` record exists (`docs/releases/`
   absent), so no released version is affected and no notification is needed (§9.3).
2. **[MEDIUM] TS-013 (stays 1.2, `in_review`).** Scope now lists SI-DEVINFRA `U-INF-CIPipeline`
   (`infra/check_image_pins.py`) as a software item under test; a class B unit acceptance criterion
   for the script was added; the Notes reword TC-013.1..4 as review and TC-013.5/.6 as automated unit
   verification; a `level:unit` tag exists; the version-history entry mentions the unit.
3. **[LOW] Fail closed.** Tests and fixtures first (`compose_empty_image.yml`,
   `workflow_container_shorthand.yml`; 2 new tests, both failed before the change). In
   `infra/check_image_pins.py` `image_values()`: an empty `image:` value (next line, or comment only)
   is reported with the reference `<empty>`; a block scalar (`image: >-`) is reported as written; the
   workflow shorthand `container: <ref>` is checked, `container:` with no value (mapping form) is not
   a finding. A comment directly after the key is now stripped. Wording updated in this task
   (Implementation detail), PRB-001 Resolution, ADD-024 and TS-013 (TC-013.6 now lists 11 tests).
4. **[LOW] Digest-only references.** Regex unchanged. TC-013.5 states that only the digest is
   enforced, that the release-tag half of AC-1 stays an inspection, and that `repo@sha256:…` passes.

Re-run: `python3 -m unittest discover -s infra/tests -v` gives 11 tests, OK;
`python3 infra/check_image_pins.py` exits 0; `cd backend && uv run pytest -q` gives 495 passed;
the four records' frontmatter parses (TASK-156 `approved`, ADD-024 and TS-013 `in_review`, PRB-001
`resolved`). The earlier evidence table above (9 tests) predates these fixes.
