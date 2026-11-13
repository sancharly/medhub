---
id: "PRB-034"
type: problem-report
title: "CI and image-build tooling is referenced by floating versions"
status: resolved
version: "1.4"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-11-12"
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

## Investigation

Re-checked against the tree on 2026-11-12 (branch `bug/build-hygiene`, after CR-001 to CR-004).
The defect stands and is slightly wider than observed:

- **GitHub Actions** are still referenced by major tag in all eight jobs of
  `.github/workflows/ci.yml`: `actions/checkout@v4` (lines 15, 85, 122, 148, 183, 225, 246, 315),
  `actions/setup-python@v5` (18, 88, 186, 282) and `actions/setup-node@v4` (125, 151, 198).
- **CI runtimes** are set without a patch version: `python-version: "3.12"` (20, 90, 188, 284),
  while the shipped runtime is Python 3.12.15 (SOUP-001, `backend/Dockerfile:1` and `:9`);
  `node-version: "24"` (127, 153, 200), while the frontend build image is
  `node:24.22.2-trixie-slim` (`frontend/Dockerfile:1`). The Node major moved from 20 to 24 with
  CR-003 (PRB-035, resolved); the missing patch version did not change.
- **uv** is installed with no version in `backend/Dockerfile:3` (`RUN pip install uv`) and in
  **four** CI jobs, not three: `backend-quality` (23), `backend-tests` (93), `openapi-lint` (191)
  and `object-store-integration` (287), the last added by CR-002 (TASK-179).
- **Mechanism.** The CR-001 pin check (`infra/check_image_pins.py`) looks only at container image
  references, and SR-028 AC-5 requires exact versions only for components that the deployed
  software ships or needs at runtime. No requirement and no check covered the tools that build and
  verify the software, so nothing stopped a moving reference.
- `backend/Dockerfile:7` installs with `uv sync --frozen --no-dev`, which installs exactly the
  locked set. A uv release could still change how the lock is read or what it installs. This is
  unlikely, but nothing excludes it.
- Out of the defect: `.pre-commit-config.yaml` hook revisions (developer tooling; CI does not run
  pre-commit) and `npm ci` (npm comes from the digest-pinned build image, and the packages from
  `package-lock.json`).

## Safety evaluation

No effect on data integrity, a safety-related function or a clinical decision is realized. The
shipped dependencies are fixed by the committed lock files and the image digests. The only
floating tool that takes part in assembling the shipped image is `uv` in `backend/Dockerfile`, and
it installs the frozen lock. The effect is on build reproducibility (§5.8.5, RR-010) and on whether
the verification evidence applies to the released build. Hence `minor`, unchanged. No `release`
record exists, so no released version is affected and no notification is needed.

## Proposed resolution

Pin GitHub Actions by commit SHA (with the version in a comment), set full patch versions for
`python-version` and `node-version`, and install a pinned `uv` version in `backend/Dockerfile`.
Needs a task and a CR.

## Resolution

Fixed by CR-005 in three tasks on branch `bug/build-hygiene`, each committed after QA approval:

- **TASK-209** (`2f68c42`): `.github/workflows/ci.yml` references `actions/checkout`,
  `actions/setup-python` and `actions/setup-node` by commit SHA with the release tag in a comment
  (15 `uses:` lines), sets `python-version: "3.12.15"` (4) and `node-version: "24.22.2"` (3), the
  patch versions of the base images in `backend/Dockerfile` and `frontend/Dockerfile`, and pins the
  OpenAPI linter that the investigation did not list (`npx --yes @redocly/cli@2.77.0`, CR-005 F-1).
- **TASK-210** (`ee02f45`): `uv==0.13.7` in `backend/Dockerfile:3` and in the four CI jobs that
  install it. `uv lock --check` passes with it, and the image built before and after holds the same
  57 distributions.
- **TASK-211** (the commit after `ee02f45` on this branch, made after its QA approval): `infra/check_image_pins.py` fails CI,
  naming file and line, when an action has no 40-hex SHA, when a `python-version` or `node-version`
  has no patch version (or reads it from a `*-version-file`) or differs from its base image, when a
  `uv` install is not `uv==X.Y.Z` or differs from the one in `backend/Dockerfile`, when
  `astral-sh/setup-uv` is used, when a `docker://` reference has no digest, and when an `npx`
  package has no exact version. This is the control against
  the mechanism found above (no check covered the tools that build and verify the software).

Why this approach: pinning to the versions in use makes the build reproducible without upgrading
anything (CR-005 A-5), and extending the existing pin check (ADR-0020) means a later edit cannot
bring a floating reference back unnoticed.

Verification (reproducible from the branch): `python3 -m unittest discover -s infra/tests -v`
(135 tests, OK; TS-013 TC-013.11); `python3 infra/check_image_pins.py` exits 0; in a scratch copy of
the repository, reverting each pin makes it exit 1 at that file and line (negative control,
recorded in TASK-211); `cd backend && uvx --from uv==0.13.7 uv lock --check` exits 0. The hosted-run
logs (Python 3.12.15, Node.js 24.22.2, uv 0.13.7) are recorded in TASK-216 (TS-013 TC-013.12). QA
approved TASK-211 on 2026-11-12 (round 2: unit tests, repository check, negative control and
`uv lock --check` re-run by QA), so the status is `resolved` (CR-005 AC-11); `closed` follows a
shipped release.

## Source

Raised during the Specify stage of CR-001 (2026-10-22), which leaves it out of scope.

## Version history

- 1.1 (2026-11-12) — `## Investigation` added for CR-005 (Specify stage): the defect is confirmed at the current tree; uv is unpinned in four CI jobs, not three; the Node major is now 24 (CR-003), still without a patch version. Criticality unchanged.
- 1.2 (2026-11-12) — `## Resolution` written for CR-005 (TASK-209, TASK-210, TASK-211). Status unchanged until QA approves TASK-211.
- 1.3 (2026-11-12) — TASK-211 sentence and test count updated after QA round 1. Status unchanged.
- 1.4 (2026-11-12) — `open → resolved` after QA approved TASK-211 (round 2; CR-005 AC-11). Closing sentence and TASK-211 commit reference updated. Criticality unchanged.
