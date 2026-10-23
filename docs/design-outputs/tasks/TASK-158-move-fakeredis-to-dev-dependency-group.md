---
id: "TASK-158"
type: task
title: "Move fakeredis to the dev dependency group"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
links:
  - target: "SR-028"
    relation: implements
  - target: "TASK-157"
    relation: relates_to
tags: ["soup", "configuration-management", "cr:CR-001", "issue:sancharly/medhub#26"]
---

# TASK-158 — Move fakeredis to the dev dependency group

- **Software item / unit:** SI-DEVINFRA `U-INF-Toolchain`, `U-INF-CIPipeline` (ADD-024); the
  backend runtime image
- **Depends on:** TASK-157 (same `pyproject.toml`, `uv.lock` and CI step; merge after it), as a
  `relates_to` link
- **Branch:** `bug/soup-pinning`

## Objective

Resolve PRB-033: `fakeredis` is a `[project]` runtime dependency although only the test suite
imports it, so an unused, unreviewed in-memory Redis imitation ships in the production image
(SOUP-018). Move it to the `dev` group so the production image no longer contains it, and retire
SOUP-018. No risk control depends on `fakeredis`. The change removes the misconfiguration path
toward RISK-005 and RISK-007 described in CR-001's risk impact, so the task has no `mitigates` link.

## Interfaces to honor

- The tests keep importing `fakeredis` (`tests/auth/test_session_service.py`,
  `tests/auth/test_lockout.py`, `tests/identity/test_erasure.py`, `tests/identity/test_lifecycle.py`).
  CI's `uv sync --frozen` installs the `dev` group by default, so they keep working. TS-001's
  environment statement ("fakeredis substitutes Redis") stays true.
- No file under `backend/app/` or `backend/modules/` may import it (none does today).

## Implementation detail

- `backend/pyproject.toml`: remove `"fakeredis>=2.36.2"` from `[project] dependencies`; add the
  same specifier to `[dependency-groups] dev`.
- `cd backend && uv lock` without `--upgrade`. In `git diff backend/uv.lock`, `fakeredis` must stay
  at 2.36.2 and move to the dev group. `sortedcontainers` may become dev-only. Any other version
  change is out of scope: revert it.
- `.github/workflows/ci.yml`, job `build`, step "Check production dependency set" (from
  TASK-157): extend the command to also fail when `fakeredis` is present:
  `docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.util, sys; import boto3; sys.exit(importlib.util.find_spec('fakeredis') is not None)"`.
- **SOUP-018** → `status: obsolete`, `version` 1.1, approval record removed. Replace the PRB-033
  note with "No longer shipped: moved to the `dev` dependency group (PRB-033, CR-001). Development
  tooling that is not shipped is not SOUP." Change log:
  `2026-10-22 — removed from the runtime dependency set (dev group only); record obsolete; PRB-033, CR-001`.
  No anomaly review is required for an obsolete record (TASK-154 skips it).
- **Do not** edit RISK-010 here. Its `relates_to` link to SOUP-018 is removed in TASK-159
  together with the rest of the RISK-010 revision, so the approved record is revised once. Until
  then, a `traceability-check` warning about a link to an obsolete record is expected.
- **TS-013** (at 1.2): extend `TC-013.8` so its expected result also says `fakeredis` is absent
  from the production image.
- **ADD-024** (at 1.1): the dependency-set step description includes the `fakeredis` absence check.
- **PRB-033** → `status: resolved`, `version` 1.1. Rewrite its `## Resolution` (today a proposal)
  as the actual resolution: the changed files, and the verification (TC-013.8, the local `--no-dev`
  check below, backend suite passing).

## Tests (write first)

Extend the CI step first and run it against the current image: it must exit 1 while `fakeredis`
is still a runtime dependency. After the manifest change it exits 0.

## Acceptance criteria

- [x] CR-001 **AC-9**: `fakeredis` absent from `[project] dependencies`, present in `dev`;
      `uv.lock` refreshed; a `uv sync --frozen --no-dev` environment does not contain it.
- [x] CR-001 **AC-10**: SOUP-018 `status: obsolete`, bumped `version`, change-log entry citing
      PRB-033 and CR-001.
- [x] CR-001 **AC-17** (PRB-033 part): PRB-033 `resolved` with its `## Resolution`.

## Verification

```sh
cd backend && uv lock --check
cd backend && UV_PROJECT_ENVIRONMENT="$(mktemp -d)/venv" sh -c 'uv sync --frozen --no-dev && "$UV_PROJECT_ENVIRONMENT/bin/python" -c "import importlib.util, sys; import boto3; sys.exit(importlib.util.find_spec(\"fakeredis\") is not None)"'; echo "exit=$?"   # expect 0
docker build -t medhub-backend:ci ./backend && docker run --rm --entrypoint python medhub-backend:ci -c "import importlib.util, sys; import boto3; sys.exit(importlib.util.find_spec('fakeredis') is not None)"
cd backend && uv run pytest
```

## Definition of Done

- [ ] Backend lint, type check and suite pass; CI Docker Build job green
- [x] SOUP-018 `obsolete`; TS-013 and ADD-024 `in_review`; PRB-033 `resolved`
- [x] `traceability-check` shows no error for the touched records (the RISK-010 → SOUP-018
      warning is expected until TASK-159)

## Carried-over QA findings from TASK-157

Both were raised in the QA review of TASK-157 (2026-10-22), touch the files this task edits, and
are fixed here. They are not acceptance criteria of TASK-158.

1. **[MEDIUM] `uv lock --check` was not run in CI.** CR-001 "Verification approach" lists
   `uv lock --check` among the static checks run in CI, but the jobs install with
   `uv sync --frozen`, which does not compare the lock with the manifest. Fixed: job
   `backend-quality` gains the step "Check the lock file is current" (`working-directory: backend`,
   `run: uv lock --check`) after "Install uv" (`.github/workflows/ci.yml`). TS-013 TC-013.7 now
   cites that step instead of a manual run; ADD-024 lists it.
2. **[LOW] TS-007's preconditions did not cover TC-007.5.** Fixed: the build is now branch
   `bug/soup-pinning`, and the preconditions say "TC-007.5 builds the real boto3 S3 client from the
   locked SDK; no object-storage service is needed." TS-007 stays 1.1 / `in_review`, its 1.1
   history entry extended.

## Implementation notes and evidence

Handed to QA on 2026-10-22 (status `in_review`). Checkboxes are left for QA.

**Files.** Changed: `backend/pyproject.toml`, `backend/uv.lock`, `.github/workflows/ci.yml` (job
`build`, step "Check production dependency set"; job `backend-quality`, new step "Check the lock
file is current"), `docs/soup/SOUP-018-fakeredis.md` (1.1, `obsolete`, approval record cleared),
`docs/design-outputs/tests-specifications/TS-013-lifecycle-record-and-traceability.md` (extends its
1.2 entry: TC-013.7 procedure, TC-013.8 expected result), `docs/design-outputs/architecture/ADD-024-development-and-verification-infrastructure.md`
(extends its 1.1 entry), `docs/design-outputs/tests-specifications/TS-007-clinical-entries-and-attachment.md`
(extends its 1.1 entry), `docs/problem-reports/PRB-033-fakeredis-shipped-as-runtime-dependency.md`
(`resolved`, 1.1), and this task. No new files; no application or test code changed.

**Lock diff.** `uv lock` without `--upgrade`: "Resolved 86 packages". `git diff --stat`: 2
insertions, 2 deletions, all in the `medhub-backend` package entry: `fakeredis` leaves
`dependencies` and `requires-dist`, and joins `[package.dev-dependencies]` and
`[package.metadata.requires-dev]`. `fakeredis` stays at 2.36.2. No package was added, removed or changed in version, and
`sortedcontainers` keeps its entry (the lock records no per-package group, so nothing changed for
it; it simply no longer reaches a `--no-dev` environment through `fakeredis`).

**Design points.**
- The CI command is exactly the one in the task: one step, one `python -c`, exit 1 when
  `fakeredis` is present, and a missing `boto3` raises.
- Tests-first: the extended command was run against the image built from the unfixed manifest and
  exited 1 before the manifest change.
- RISK-010 was not touched (its link to SOUP-018 goes in TASK-159). Per the task, an interim
  `traceability-check` warning for that link is expected.
- Besides the "Interfaces to honor" list, `backend/tests/api/test_lockout_integration.py` and
  `backend/tests/workers/test_session_revoke.py` also import `fakeredis`. Both are tests, so the
  dev group covers them; the task's list of four files was incomplete, not wrong in effect
  (recorded in PRB-033 Investigation).
- SOUP-018's body: besides the note and change log required by the task, the "Functional and
  performance requirements" and "Anomaly list review" paragraphs were reworded because they said
  the item ships and that its review is pending, which is no longer true.

**Verification run (2026-10-22, macOS, branch `bug/soup-pinning`).**

| Command | Result |
|---|---|
| Extended CI command against the image built before the manifest change | exit 1 |
| `cd backend && uv lock` then `uv lock --check` | 86 packages; only group membership of `fakeredis` changed; check exit 0 |
| `cd backend && uv run pytest -q` | 496 passed (fakeredis still available through the dev group) |
| `uv run ruff check .`, `uv run black --check .`, `uv run mypy app` | all pass (`219 files would be left unchanged`; `no issues found in 124 source files`) |
| `UV_PROJECT_ENVIRONMENT=<scratch>/venv uv sync --frozen --no-dev`, then the `find_spec` check | exit 0; `import fakeredis` raises `ModuleNotFoundError`; `import boto3` gives 1.43.117 |
| `docker build -t medhub-backend:ci ./backend`, then the extended CI command | build OK; exit 0 |
| The same command against the image from before the manifest change (contains fakeredis) | exit 1: the step fails closed |
| `python3 infra/check_image_pins.py`; `python3 -m unittest discover -s infra/tests` | exit 0, no output; 11 tests OK |
| `.github/workflows/ci.yml` parsed (Ruby YAML) | valid; `backend-quality` steps: checkout, Set up Python 3.12, Install uv, Check the lock file is current, Install dependencies, Ruff, Black, Mypy; `build` steps unchanged in order |

**Not verified here.** GitHub Actions cannot be run locally: the new `backend-quality` step and the
extended `build` step have been checked only by running their commands locally. The full-pipeline
green run is Checkpoint A (AC-16). `traceability-check` was not run by the developer role; QA runs
it. The frontend suite was not run (no frontend change). The scratch environment and the temporary
images used for the negative check were removed; the working tree holds only the files listed above.

## QA review (2026-10-22)

**Verdict: APPROVED** (`in_review → approved`). No CRITICAL or HIGH finding. Both TASK-157 follow-ups
are resolved (see below).

**Records that stay `in_review`:**
- TS-013 and ADD-024, for the human. TASK-159 extends TS-013 under 1.2.
- TS-007. The content is now sound and no later CR-001 task touches it: CR-001's plan gives
  TASK-154 the SOUP records and TASK-159 RISK-010 and TS-013, and neither task record names TS-007.
  But CR-001 AC-18 requires every record the CR changes to be `in_review` when TASK-159 checks it.
  Approving TS-007 now would fail that check, and it would be inconsistent with TS-013, which is kept
  `in_review` for the same reason. So the human approves TS-007 with the other CR-001 records. This
  replaces the TASK-157 review's note that TS-007 "can go to `approved` once that fix is in".

**Definition of Done:** "CI Docker Build job green" stays open. Lint, type check and suite pass
locally. The CI run on the branch head is Checkpoint A (AC-16).

### TASK-157 follow-ups

- **[MEDIUM] `uv lock --check` in CI — resolved.**
  - `.github/workflows/ci.yml:25-27`: job `backend-quality`, step "Check the lock file is current",
    with `working-directory: backend` and `run: uv lock --check`.
  - It runs after "Install uv" and before "Install dependencies". The YAML parses.
  - QA checked it both ways: it exits 0 on the branch and exits 1 on a scratchpad copy whose
    manifest gained an unlocked dependency.
  - TS-013 TC-013.7 and ADD-024 now cite the step.
- **[LOW] TS-007 preconditions — resolved.** `TS-007…md:30` names the build as `bug/soup-pinning`
  and says that TC-007.5 builds the real boto3 client and needs no object-storage service. The 1.1
  history entry is extended.

### Findings

- **[LOW] TS-013 still files TC-013.7 under the "review" level.**
  `docs/design-outputs/tests-specifications/TS-013-lifecycle-record-and-traceability.md:26` reads
  "Levels: review (TC-013.1 to TC-013.4, TC-013.7)". TC-013.7 is now an automated CI check.
  → In TASK-159, which extends TS-013 anyway, move TC-013.7 out of "review", for example
  "static check (TC-013.7)", or list it with TC-013.5.
- **[LOW] The new lock check runs on an unpinned `uv`, and PRB-034 does not list CI's uv install.**
  `.github/workflows/ci.yml:22-23` (also `:92-93` and `:180-181`) run `pip install uv` with no
  version. `uv lock --check` now gates `backend-quality`. A uv release that changes the lock output
  would fail the job with no code change. That is fail-closed, so it is not unsafe, but it could
  block merges spuriously. PRB-034 lists only `backend/Dockerfile`'s `pip install uv`.
  → Add CI's `pip install uv` to PRB-034 "Observed" (a record update outside this task), or pin
  `uv==0.11.23` in the three CI installs when PRB-034 is worked.

Observations (no action needed):
- `sys.exit(find_spec('fakeredis') is not None)` exits 1 when the package is present and 0 when it
  is absent. A missing `boto3` raises before that, so the step fails closed on either fault.
- `redis` stays a direct runtime dependency. `sortedcontainers` is reached only through
  `fakeredis`, so it is now dev-only too. It has no SOUP record of its own (SOUP-018's
  transitive).
- PRB-033's Investigation gives the dev group as `:26-35`. It is `:26-36` at `c455618`, which is
  immaterial.
- SOUP-018's Monitoring paragraph still describes ongoing monitoring, which no longer applies to an
  obsolete record. Harmless.
- The fallback parser reports `soup_unintegrated` and `soup_anomaly_review_stale` for SOUP-018.
  It does not exempt `obsolete` records. CR-001 AC-18 and the overlay apply those rules to SOUP in
  use only, so these are not gaps.

### Verification run (QA, 2026-10-22, macOS, uv 0.11.23, Docker)

| Command | Result |
|---|---|
| `git diff backend/pyproject.toml` | `"fakeredis>=2.36.2"` leaves `[project] dependencies` and is added to `[dependency-groups] dev` with the same bound |
| `tomllib` comparison of `uv.lock` with `HEAD` (`c455618`) | no package added, removed or changed. `fakeredis` stays 2.36.2. The diff (2+/2−) only moves it within the `medhub-backend` entry, `dependencies` → `dev-dependencies` and `requires-dist` → `requires-dev` |
| `cd backend && uv lock --check` | `Resolved 86 packages`, exit 0 |
| `uv lock --check` on a scratchpad copy with an unlocked `six>=1.16` added | exit 1, "needs to be updated" |
| `grep -rn fakeredis app modules scripts entrypoint.sh` | none. Six test files import it, matching PRB-033's line references |
| `uv sync --frozen --no-dev` into a scratch venv, then the CI `find_spec` command | exit 0. `fakeredis` and `sortedcontainers` are absent; `redis` and `boto3` are present |
| `docker build -t medhub-backend:ci ./backend`, then the step's `run:` string taken from the parsed YAML | exit 0 |
| The same string against an image built from `git archive HEAD backend`, which holds fakeredis 2.36.2 | exit 1 |
| `ci.yml` parsed (Ruby YAML) | `backend-quality`: checkout → Set up Python 3.12 → Install uv → Check the lock file is current (`working-directory: backend`) → Install dependencies → Ruff → Black → Mypy. `build` step order unchanged |
| `uv run pytest --cov=app --cov-fail-under=85 -q` | `496 passed`, coverage 91.71 % |
| `ruff check .`, `black --check .`, `mypy app` | pass; 219 files unchanged; no issues in 124 source files |
| `python3 infra/check_image_pins.py`, `python3 -m unittest discover -s infra/tests` | exit 0, no output; OK (11 tests) |
| `traceability-check` (fallback parser) on TASK-158, SOUP-018, TS-013, TS-007, ADD-024, PRB-033, CR-001, links resolved against all 329 records | **0 errors.** SOUP-018 `soup_unintegrated` and `soup_anomaly_review_stale` are parser artefacts for an obsolete record (see above). On RISK-010: W6 → obsolete SOUP-018 (expected until TASK-159), and W5 → the `in_review` SOUP records (expected, CR-001 AC-18). E9 holds for PRB-033 (CR-001 `resolves`) |
| Records review | **SOUP-018:** `obsolete`, 1.1, approval record cleared, change log cites PRB-033 and CR-001 (AC-10). **PRB-033:** Investigation with `file:line` references; Safety evaluation with RISK-005 and RISK-007, `minor`, no release, no notification; Resolution with files and reproducible commands. **TS-013 TC-013.8:** extended with the absence of `fakeredis` (AC-15 part). **ADD-024:** accurate for both steps |

Pending, not blocking: the first CI run of both changed steps on the branch head (AC-16, Checkpoint A).
