---
id: "TASK-209"
type: task
title: "Pin GitHub Actions, CI runtimes and the OpenAPI linter to exact versions"
status: approved
version: "1.1"
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
  - target: "SOUP-001"
    relation: relates_to
tags: ["ci", "reproducibility", "cr:CR-005", "control:design"]
---

# TASK-209 — Pin GitHub Actions, CI runtimes and the OpenAPI linter to exact versions

- **Software item / unit:** SI-DEVINFRA `U-INF-CIPipeline` (ADD-024).
- **PRB:** PRB-034. **CR:** CR-005 (AC-1, AC-2; finding F-1 of the change analysis).
- **Depends on:** none. Ordered before TASK-210 (same file) and TASK-211 (its check runs on the
  pinned file).
- **Branch:** `bug/build-hygiene`.
- **Size:** S (`.github/workflows/ci.yml` only).

## Objective

SR-028 AC-8 for the workflow: every action by a 40-hex commit SHA with its release tag in a trailing
comment; every `python-version` and `node-version` at the patch version of the matching base image;
the OpenAPI linter that `npx` downloads at an exact version. Pinning records the versions in use
(CR-005 A-5); nothing is upgraded.

## Implementation detail

1. **Actions** (`actions/checkout`, `actions/setup-python`, `actions/setup-node`; 15 `uses:` lines
   at HEAD): `uses: actions/checkout@<40-hex> # vX.Y.Z`. The SHA is the one the hosted run of
   2026-11-10 (run 42779806388) resolved for the major tag in use, read from the job log line
   "Download action repository": checkout `11d5960a326750d5838078e36cf38b85af677262`,
   setup-python `a26af69be951a213d495a4c3e4e4022e16d87065`, setup-node
   `49933ea5288caeca8642d1e84afbd3f7d6820020`. For each, find the exact release tag that points at
   that commit (`git ls-remote --tags https://github.com/actions/<name>` and match the SHA, peeled
   `^{}` entries included) and write it in the comment. If a SHA matches no exact release tag, stop
   and ask (CR-005 Boundaries: no version change without asking).
2. **Python:** `python-version: "3.12.15"` in all four jobs (SOUP-001, `backend/Dockerfile:1`).
   The step names "Set up Python 3.12" become "Set up Python 3.12.15".
   **CR-005 A-3 holds:** `actions/python-versions` `versions-manifest.json` lists 3.12.15 (stable)
   for linux x64 on Ubuntu 22.04, 24.04 and 26.04 (checked 2026-11-12); the runner is
   `ubuntu-26.04` (run 42779806388). No fallback (`uv python install`) is needed.
3. **Node.js:** `node-version: "24.22.2"` in all three places (`frontend/Dockerfile:1`,
   `node:24.22.2-trixie-slim`). Step names follow.
4. **OpenAPI linter (F-1):** `npx --yes @redocly/cli lint` becomes
   `npx --yes @redocly/cli@X.Y.Z lint`, where X.Y.Z is the latest version published on the npm
   registry before the run of 2026-11-10 08:05 UTC (`npm view @redocly/cli time --json`), i.e.
   the version that produced the last green evidence. Record the lookup.
5. `runs-on` is not changed unless the human answers CR-005 Q-6 otherwise.

## Tests (write first)

None of its own: the automated check is TASK-211, which turns every rule here into a failing
fixture first. This task's evidence is the hosted run and the SHA-to-tag record.

## Acceptance criteria

- [x] CR-005 AC-1: every `uses:` names a 40-hex SHA with the release tag in a comment; the
      SHA-to-tag check for each of the three actions is recorded below.
- [x] CR-005 AC-2: every `python-version` is `3.12.15` and every `node-version` is `24.22.2`.
- [x] F-1: the `npx` call names `@redocly/cli@X.Y.Z`, and the version lookup is recorded.

## Verification

```sh
grep -nE '^\s*(- )?uses:' .github/workflows/ci.yml          # every line: @<40 hex> # vX.Y.Z
grep -nE 'python-version|node-version|npx ' .github/workflows/ci.yml
git ls-remote --tags https://github.com/actions/checkout | grep 11d5960a326750d5838078e36cf38b85af677262
git ls-remote --tags https://github.com/actions/setup-python | grep a26af69be951a213d495a4c3e4e4022e16d87065
git ls-remote --tags https://github.com/actions/setup-node | grep 49933ea5288caeca8642d1e84afbd3f7d6820020
python3 -m unittest discover -s infra/tests     # test_ci_compose_env.py reads ci.yml
python3 infra/check_image_pins.py               # unchanged rule set: still exit 0
```

After the push (TASK-216): the hosted log of every Python job shows `Python 3.12.15`, every Node
job `v24.22.2`, and the OpenAPI Lint job the pinned linter version.

## Implementation evidence (2026-11-12)

Changed: `.github/workflows/ci.yml` only (30 lines: 15 `uses:`, 4 `python-version`, 3
`node-version`, 7 step names, 1 `npx` call). `runs-on: ubuntu-latest` unchanged (CR-005 Q-6 not
answered otherwise).

SHA-to-tag check (`git ls-remote --tags` match, then `gh api repos/actions/<name>/git/ref/tags/<tag>`;
all three refs are lightweight tags, `object.type` = `commit`, so no dereferencing is needed):

| Action | SHA (run 42779806388) | Exact release tag | `gh api` result |
|---|---|---|---|
| `actions/checkout` | `11d5960a326750d5838078e36cf38b85af677262` | `v4.4.0` (also `v4`) | commit, same SHA |
| `actions/setup-python` | `a26af69be951a213d495a4c3e4e4022e16d87065` | `v5.6.0` (also `v5`) | commit, same SHA |
| `actions/setup-node` | `49933ea5288caeca8642d1e84afbd3f7d6820020` | `v4.4.0` (also `v4`) | commit, same SHA |

OpenAPI linter lookup (`npm view @redocly/cli time --json`; run 42779806388 started
2026-11-10T08:04:31Z): latest non-prerelease before the run is `2.77.0` (published
2026-11-09T09:58:44Z); the next release, `2.78.0`, is dated 2026-11-12T15:05:34Z. (`1.34.24`,
2026-11-05, is a 1.x backport and not the `latest` line.) The call is
`npx --yes @redocly/cli@2.77.0 lint openapi.json`.

Verification run: `grep` of `uses:` shows all 15 lines as `@<40 hex> # vX.Y.Z`; `python-version`
is `"3.12.15"` x4 and `node-version` `"24.22.2"` x3; `python3 -m unittest discover -s infra/tests`
OK (114 tests); `python3 infra/check_image_pins.py` exit 0. `actionlint` and PyYAML are not
installed locally, so the workflow was not linted; the hosted run (TASK-216) is the check.

## QA review (2026-11-12): APPROVED

No CRITICAL or HIGH finding. The hosted-log checks under Verification ("After the push") belong to
TASK-216.

### Findings

1. **LOW: the record says 2.77.0 "produced the last green evidence"; the hosted log does not show
   that.** This record, Implementation evidence, OpenAPI linter paragraph. The OpenAPI Lint log of
   run 42779806388 prints `npx --yes @redocly/cli lint openapi.json` and the lint result, but no
   linter version. 2.77.0 is the latest non-prerelease published before the run (npm `time`: 2.77.0
   2026-11-09T09:58:44Z, next 2.78.0 2026-11-12T15:05:34Z; only `0.0.0-snapshot.*` builds between,
   which are not on the `latest` line). That fits the plan-gate decision ("the redocly release
   before that run"), but it is an inference from the publication dates, not something the log
   shows. → When TASK-216 reads the hosted log, check that the OpenAPI Lint result (warning count
   and rules) is the same as in run 42779806388. If it differs, open a PRB rather than move the pin.

### Verification run

- `git diff --stat`, `git status --porcelain`: the only source change on the branch is
  `.github/workflows/ci.yml`, with 30 lines changed (15 `uses:`, 7 step names, 4 `python-version`,
  3 `node-version`, 1 `npx`). Every other change is a CR-005 record. `runs-on` is unchanged (Q-6).
- SHA-to-tag, checked independently. `git ls-remote --tags`: checkout `11d5960a…7262` = `v4`,
  `v4.4.0`; setup-python `a26af69b…7065` = `v5`, `v5.6.0`; setup-node `49933ea5…0020` = `v4`,
  `v4.4.0`. `gh api repos/actions/<name>/git/ref/tags/<tag>`: all three are `commit` objects with
  the same SHA. The comment on every `uses:` names the matching tag.
- Run 42779806388 (`gh run view --log`; head `d53eb7f`, all 8 jobs `success`, started
  2026-11-10T08:04:31Z): every "Download action repository" line (15 in total) resolved to the same
  three SHAs. The Python jobs ran CPython 3.12.16, the Node jobs `v24.22.2`, on runner image
  `ubuntu-26.04` 20261101.186.1. So nothing is upgraded: the action SHAs and Node.js stay the same,
  and Python moves to the shipped 3.12.15 as CR-005 intends.
- AC-2 sources: `backend/Dockerfile:1,9` `python:3.12.15-slim@sha256:…`, SOUP-001
  `soup_version: 3.12.15`; `frontend/Dockerfile:1` `node:24.22.2-trixie-slim@sha256:…`. The parsed
  workflow has `python-version` `'3.12.15'` x4 and `node-version` `'24.22.2'` x3, all quoted
  strings.
- F-1: `npm view @redocly/cli time --json`, see finding 1. `npm view @redocly/cli@2.77.0 engines`
  gives node `>=22.12.0`, which 24.22.2 meets. `npx` appears only once in the workflow.
- YAML: `uv run --no-project --with pyyaml` loads the file (8 jobs, 15 `uses`); every `uses` value
  matches `actions/(checkout|setup-python|setup-node)@[0-9a-f]{40}`. `rhysd/actionlint:1.7.7`
  (Docker, shellcheck and pyflakes off): exit 0 on the new file and on HEAD.
- `python3 -m unittest discover -s infra/tests`: 114 tests, OK. `python3 infra/check_image_pins.py`:
  exit 0.
- `traceability-check` (fallback parser; no project tooling) on CR-005, TASK-209..216, SR-028,
  RISK-010 and PRB-034/038/040/041, plus everything they link to or from (103 records): **0
  errors**. 6 W6 warnings, all from links in older records to elements that are now `obsolete`
  (ADD-003 → ADD-002, CR-002 → SOUP-022/023, TASK-148 → TASK-114, TASK-165 → SOUP-033,
  TASK-176 → SOUP-022), none of them added by CR-005.

## Records

PRB-034 (resolution written by TASK-211, which completes the PRB-034 work), CR-005.

## Version history

- 1.0 (2026-11-12) — Created at the CR-005 Plan stage (Software Architect role); `draft`.
- 1.0 (2026-11-12) — Implemented at the Build stage (Software Developer role); `draft → in_review`. Boxes left unticked for QA.
- 1.1 (2026-11-12) — QA review: APPROVED (1 LOW). `in_review → approved`; AC-1, AC-2 and F-1
  ticked. The hosted-log check is TASK-216's.
