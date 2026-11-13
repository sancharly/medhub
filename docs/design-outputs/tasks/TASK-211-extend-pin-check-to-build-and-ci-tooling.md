---
id: "TASK-211"
type: task
title: "Extend the pin check to build and CI tool references"
status: approved
version: "1.3"
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
   `# v<tag>`; `./…` is exempt; `docker://…` goes to the existing image rule, which now matches `uses: docker://<image>` (round 2).
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

- [x] CR-005 AC-4: each form above fails with file and line; each pinned form passes; the check
      passes on the repository (exit 0).
- [x] Negative control: reverting one action to `@v4`, one `python-version` to `"3.12"`, one uv
      install to `pip install uv` and the linter to `@redocly/cli` each makes
      `python3 infra/check_image_pins.py` exit 1 with the right file and line (scratch copy).
- [x] Records: TS-013 gains TC-013.11 (unit, tool rules) and TC-013.12 (integration/review:
      repository run exit 0; SHA-to-tag record of TASK-209; `uv lock --check` with the pinned uv;
      hosted logs show 3.12.15, 24.22.2, uv 0.13.7); ADD-024 `U-INF-CIPipeline` describes the
      extended check and the pinned tools; PRB-034 `## Resolution` written (TASK-209..211).

## Verification

```sh
python3 -m unittest discover -s infra/tests -v
python3 infra/check_image_pins.py; echo "exit $?"      # 0
# negative control on a scratch copy of the repository, one mutation at a time
```

## Build evidence (2026-11-12)

- Changed: `infra/check_image_pins.py` (tool rules; `--root DIR`; `git_paths()` factored out of
  `tracked_files()`; argparse; docstring and `--help` list every rule),
  `infra/tests/test_check_image_pins.py` (class `ToolReferences`, helper `run_tools`, one test in
  it for PATH plus `--root`), new fixtures `infra/tests/fixtures/tools/` (`base/backend` and
  `base/frontend` Dockerfiles, 9 workflow fixtures, 2 Dockerfile fixtures). The image rule, its
  output and exit codes, and the 11 existing tests are unchanged. The CI job "Image Pin Check" is
  unchanged: it runs `python3 -m unittest discover -s infra/tests -v` and then
  `python3 infra/check_image_pins.py`, which now includes the tool rules (no flag needed).
  Records: TS-013 1.6 (`in_review`; TC-013.11, TC-013.12), ADD-024 1.3 (`in_review`), PRB-034 1.2
  (`## Resolution`), SOUP-001 1.3 (`in_review`; QA finding 1 of TASK-210).
- Tests: `python3 -m unittest discover -s infra/tests`: 126 tests, OK (114 before, 12 added).
  `python3 infra/check_image_pins.py`: exit 0, no output.
- Decisions: a `uses:` ref with no `@` is reported as an unpinned action; a version key with no
  matching `FROM python:X.Y.Z` / `FROM node:X.Y.Z` in the base Dockerfile is reported, not skipped;
  when two `uv==` versions exist, `backend/Dockerfile` (the shipped image) is the reference when it
  installs uv, otherwise the most common version, and each other occurrence is reported (changed in
  round 2, QA finding 3).
- Negative control, scratch copy (`git ls-files` plus untracked files, copied to a scratch
  directory and committed to a throwaway git repository; the working tree was not touched), one
  mutation at a time, restored after each; baseline exit 0:

  | Mutation | Output (exit 1 each) |
  |---|---|
  | `ci.yml:15` checkout back to `@v4` | `.github/workflows/ci.yml:15: action not pinned to a commit SHA: actions/checkout@v4` |
  | `ci.yml:20` `python-version: "3.12"` | `.github/workflows/ci.yml:20: python-version without a full patch version: 3.12` |
  | `ci.yml:23` `pip install uv` | `.github/workflows/ci.yml:23: uv install without an exact version: uv` |
  | `backend/Dockerfile:3` `pip install uv` | `backend/Dockerfile:3: uv install without an exact version: uv` |
  | `ci.yml:93` `uv==0.13.6` | `.github/workflows/ci.yml:93: uv version differs from the others (0.13.7): uv==0.13.6` |
  | `ci.yml:127` `node-version: "24"` | `.github/workflows/ci.yml:127: node-version without a full patch version: 24` |
  | `ci.yml:153` `node-version: "24.22.1"` | `.github/workflows/ci.yml:153: node-version differs from frontend/Dockerfile (24.22.2): 24.22.1` |
  | `ci.yml:210` linter back to `@redocly/cli` | `.github/workflows/ci.yml:210: npx package without an exact version: @redocly/cli` |

  After the last restore the scratch copy exits 0 again.
- TC-013.12: `uvx --from uv==0.13.7 uv --version` prints `uv 0.13.7`; `uv lock --check` in
  `backend/` passes ("Resolved 86 packages"). The SHA-to-tag record is in TASK-209 (QA-checked with
  `git ls-remote` and `gh api`). The hosted-log part (3.12.15, 24.22.2, uv 0.13.7 in the logs of a
  pushed run) cannot be produced before the push: it is open until TASK-216 (Checkpoint C).
- Not run: backend and frontend suites (no source of theirs changed). `infra/` is outside the ruff
  and black configuration of `backend/pyproject.toml` (the existing script and tests already fail
  `black --check` run from there), so no formatter was applied.

## Records

- **TS-013** (`approved` 1.5): the first CR-005 task that changes it bumps it to 1.6, clears the
  approval record and sets `in_review`; later CR-005 tasks add to 1.6 (CR-002 rule).
- **ADD-024** (`approved` 1.2): same rule, 1.3.
- **PRB-034**: `## Resolution` names TASK-209, 210, 211 and their commits; `resolved` only after
  QA approves this task (AC-11).

## QA review (2026-11-12): CHANGES REQUESTED

Verified by QA: `python3 -m unittest discover -s infra/tests -v` 126 tests OK;
`python3 infra/check_image_pins.py` exit 0, no output; image rule and exit codes unchanged
(missing file exit 2, `compose_unpinned.yml` exit 1 with the 4 existing lines); the `image-pins`
job (`ci.yml:311-321`) still runs the unit tests and then the script with no arguments. Negative
control reproduced in a scratch copy (tracked + untracked files in a throwaway git repository),
one mutation at a time, each exit 1 at the right file and line, exit 0 after restore:
`ci.yml:85` `@v4`; `ci.yml:125` short SHA; `ci.yml:188` `"3.12"`; `ci.yml:284` `"3.12.16"`;
`ci.yml:200` `"24"`; `backend/Dockerfile:1` base moved to 3.12.16 (all four `python-version`
lines reported); `ci.yml:191` and `backend/Dockerfile:3` `pip install uv`; `ci.yml:287`
`uv==0.13.8`; `ci.yml:210` `@redocly/cli`. Traceability (CR-005 two-hop scope, 170 of 439
records): 0 errors.

Findings (to fix before re-review):

1. **HIGH: `uses: docker://<image>` is checked by neither rule.** `infra/check_image_pins.py:215`
   returns no finding for `docker://` ("goes to the image rule", docstring line 9), but the image
   rule only matches `image:` / `container:` (`IMAGE_KEY`, line 51). Reproduced: `ci.yml:85` set
   to `uses: docker://alpine:3.20` gives exit 0 with no arguments and with the explicit path. A
   floating CI container passes, against SR-028 AC-8, ADR-0020 ("`docker://…` is checked by the
   image rule") and this task's Implementation detail 1. `uses_pass.yml:8` and TC-013.11 ("A
   `uses: docker://` … pass") record the gap as expected behaviour. Fix: report a `docker://`
   reference without `@sha256:<64 hex>` (or with `$`) with the image-rule message, preferably in
   `image_values()` so the per-file mode catches it too; failing fixture
   `uses: docker://alpine:3.20`, passing fixture with a digest; correct TC-013.11, the TS-013
   acceptance criterion (line 90) and ADD-024 line 40 ("`docker://` exempt").
2. **MEDIUM: forms that pass silently, against "A form the rules cannot parse is a finding,
   never a pass"** (docstring line 17; ADD-024; TS-013 line 90; CR-005 plan risk "Unparseable
   forms fail"). Reproduced with `--root` on scratch trees, each exit 0 / not reported:
   (a) a Dockerfile `RUN pip install --no-cache-dir \` continued by `    uv`, and the exec form
   `RUN ["pip", "install", "uv"]` (the shipped image path); (b) `python-version-file:` /
   `node-version-file:` (setup-python / setup-node read the version from a file);
   (c) `uses: astral-sh/setup-uv@<sha> # v6` with no `version:` (installs the newest uv);
   (d) `run: "npx @redocly/cli lint"` (quoted scalar) and `FOO=1 npx eslint` (env prefix).
   None occurs in the repository today. Fix: join `\`-continued lines before the uv match and
   match the JSON exec form; report `*-version-file` keys; report `astral-sh/setup-uv` (no uv
   action is used, so a finding is the fail-closed choice); match `npx` after a quote or an
   `X=Y` prefix. A fixture per form. Any form left unfixed must be listed in the TS-013
   acceptance criterion as not seen, and the "never a pass" sentence narrowed.
3. **LOW: uv reference rule differs from the recorded decision.** Build evidence says "the one
   found first (path order) is the reference"; `check_image_pins.py:201` takes the most common
   version (first only on a tie, and workflows come before Dockerfiles, so a 1:1 disagreement
   names `backend/Dockerfile`, the shipped one, as the wrong line). Exit 1 either way. Fix:
   correct the decision text, or make `backend/Dockerfile` the reference when it installs uv.
4. **LOW: `--root` on a missing or empty directory exits 0** (`root_paths`, line 154: `rglob` of
   nothing). The docstring says exit 2 on a usage error, and the image mode prints "no files to
   scan" and exits 2. Fix: exit 2 when DIR is not a directory or holds no workflow or Dockerfile;
   add a test.
5. **LOW: TS-013 line 90** says a multi-line `uses:` "is not seen"; a folded `uses: >-` is
   reported (fails closed, reference `>-`). Correct the sentence.
6. **LOW: `infra/tests/test_check_image_pins.py:273-274`** two blank lines inside the class, and
   `test_paths_and_root_together_exit_2` asserts only the exit code. Fix: one blank line; assert
   the argparse message in stderr.

Not findings (fail closed, acceptable): `npx --package=pkg@X.Y.Z bin` and
`(cd a && npx pkg@X.Y.Z)` are reported; prerelease `pkg@1.2.3-beta.1`, `uv[extra]==X.Y.Z`,
`uv===X.Y.Z`, uppercase or 39/41-hex SHAs, `v24.22.2`, `3.12.15.1` are reported; quoted and
unquoted versions both pass when exact; `pipx install uv`, `pip3`, `python -m pip`, multi-package
`pip install requests uv` are reported; a reusable workflow `owner/repo/.github/workflows/x.yml@main`
is reported; a YAML anchor body is checked on its own line. The `# v` comment is not compared with
the SHA (TC-013.12 review covers it). Composite actions (`.github/actions/**/action.yml`) are not
scanned; none exists. The developer's other two decisions (no `@` ref = unpinned; version key
without a matching `FROM` = finding, reproduced) are agreed.

Records: SOUP-001 1.3 (line 67 corrected), ADD-024 1.3 and TS-013 1.6 are version-bumped and
`in_review`, correct apart from the `docker://` wording (finding 1). PRB-034 `## Resolution` counts
check against `ci.yml` (15 `uses:`, 4 `python-version`, 3 `node-version`) and TASK-210 (57
distributions); its TASK-211 sentence must hold after finding 1. PRB-034 stays `open`.

## Round 2 (2026-11-12): response to the QA review

Tests: `python3 -m unittest discover -s infra/tests -v`: 135 tests, OK (126 before, 9 added).
`python3 infra/check_image_pins.py`: exit 0, no output.

| Finding | Fix |
|---|---|
| 1 HIGH `docker://` | `image_values()` also matches `uses: [quoted] docker://<image>` (`DOCKER_USES`); a reference without `@sha256:<64 hex>` or with `$` is reported with the image-rule message, in the default mode and in per-file mode. Fixtures `workflow_docker_uses_unpinned.yml` (3 findings: plain, quoted, `${{ }}`) and `workflow_docker_uses_pinned.yml`; the `docker://` line is removed from `tools/uses_pass.yml` (`--root` runs the tool rules only). TC-013.11, TS-013 acceptance criterion, ADD-024, docstring corrected. |
| 2 MEDIUM silent forms | All fixed, none left unfixed: `\`-continued lines joined (`logical_lines`, reported at the first physical line) and Dockerfile exec form read (`Dockerfile.uv_forms_fail` / `_pass`); `python-version-file` / `node-version-file` reported (`versionfile_fail.yml`); `astral-sh/setup-uv` reported even when pinned (decision: report, not "require `version:` equal to the pin", because the rule then has no second place to compare; `setup_uv_fail.yml`); `npx` after a quote or a `VAR=value` prefix (`npx_forms_fail.yml`, passing forms added to `npx_pass.yml`). The "never a pass" claim is narrowed to "forms of the kinds above", and TS-013 / ADD-024 / docstring list what is not seen: an `npx` or `pip install uv` reached through a script file, a command assembled by a YAML anchor or template, composite actions under `.github/actions/` (none in the repository). |
| 3 LOW uv reference | `backend/Dockerfile` is the reference when it installs uv (most common version otherwise); decision text above updated; tests `test_backend_dockerfile_is_the_uv_reference` (replaces the second half of `test_two_uv_versions_in_one_repository_fail`, whose expectation named the Dockerfile as the wrong line). |
| 4 LOW `--root` | Missing directory or no workflow or Dockerfile under it: stderr message, exit 2; test `test_root_missing_or_without_workflows_or_dockerfiles_exits_2`. |
| 5 LOW TS-013 multi-line | Sentence corrected: a folded `uses: >-` is reported (reference `>-`, fails closed); only script-file, anchor and composite-action forms are listed as not seen. |
| 6 LOW test file | Extra blank line removed; `test_paths_and_root_together_exit_2` asserts `PATH and --root cannot be combined` in stderr. |

Records: PRB-034 1.3 (`open`; Resolution sentence and test count updated), TS-013 and ADD-024 stay
at 1.6 / 1.3 `in_review` (same pending version).

Negative control, scratch copy again (tracked plus untracked files, throwaway git repository,
working tree untouched; baseline exit 0; restored with `git checkout` after each; each mutation
printed the finding below and exited 1):

| Mutation | Output |
|---|---|
| `ci.yml:15` `uses: docker://alpine:3.20` | `ci.yml:15: image reference without @sha256 digest: docker://alpine:3.20` |
| `ci.yml:15` `@v4` | `ci.yml:15: action not pinned to a commit SHA: actions/checkout@v4` |
| `ci.yml:15` `astral-sh/setup-uv@<sha> # v6.4.3` | `ci.yml:15: uv installed by an action, outside the uv==X.Y.Z rule: astral-sh/setup-uv@…` |
| `ci.yml:20` `"3.12"` | `ci.yml:20: python-version without a full patch version: 3.12` |
| `ci.yml:20` `python-version-file: .python-version` | `ci.yml:20: python-version-file cannot be compared with the base image: .python-version` |
| `ci.yml:23` `pip install uv` | `ci.yml:23: uv install without an exact version: uv` |
| `backend/Dockerfile:3` `pip install --no-cache-dir \` + `    uv` | `backend/Dockerfile:3: uv install without an exact version: uv` |
| `backend/Dockerfile:3` `RUN ["pip", "install", "uv"]` | `backend/Dockerfile:3: uv install without an exact version: uv` |
| `ci.yml:93` `uv==0.13.6` | `ci.yml:93: uv version differs from the others (0.13.7): uv==0.13.6` |
| `backend/Dockerfile:3` `uv==0.13.6` | `ci.yml:23, 93, 191: uv version differs from the others (0.13.6): uv==0.13.7` (the shipped image is the reference) |
| `ci.yml:210` `@redocly/cli` | `ci.yml:210: npx package without an exact version: @redocly/cli` |
| `ci.yml:210` `run: "npx --yes @redocly/cli lint …"` | same finding, quoted form |

After the last restore the scratch copy exits 0. Not run: backend and frontend suites (no source of
theirs changed).

## QA review round 2 (2026-11-12): APPROVED

Verified by QA: `python3 -m unittest discover -s infra/tests -v` 135 tests OK;
`python3 infra/check_image_pins.py` exit 0, no output. The image rule is unchanged: the HEAD and
working-tree scripts give identical output and exit code, file by file, on every fixture outside
`tools/` and on every tracked Compose file, Dockerfile and workflow; missing file exit 2.

Round-1 findings, each reproduced and now fixed:

1. `uses: docker://` without a digest: exit 1 with the image-rule message in the default mode
   (scratch copy, `ci.yml:15` set to `docker://alpine:3.20`) and in per-file mode
   (`workflow_docker_uses_unpinned.yml`: 3 findings, lines 4-6; `_pinned.yml` exit 0).
2. Continued-line and exec-form uv installs, `*-version-file`, `astral-sh/setup-uv`, quoted and
   `VAR=` npx: each reported at the first physical line (scratch tree with `--root`, and the
   negative control below). A trailing `\` on the last line of a file is reported, not lost.
3. `backend/Dockerfile` is the uv reference: `backend/Dockerfile:3` set to `uv==0.13.6` reports
   `ci.yml:23, 93, 191` **and 287** (the Round 2 table omits 287).
4. `--root` on a missing directory, an empty one, or one with only a Compose file: stderr
   message, exit 2.
5. TS-013 acceptance criterion: the folded `uses: >-` wording is corrected.
6. Test file: no double blank line inside a class; `test_paths_and_root_together_exit_2` asserts
   the argparse message.

Negative control re-run by QA on a scratch copy (tracked plus untracked files, throwaway git
repository; baseline exit 0; `git checkout .` after each), exit code captured per mutation:
`ci.yml:15` `docker://alpine:3.20` 1; `@v4` 1; `astral-sh/setup-uv@<sha> # v6.4.3` 1; `ci.yml:20`
`"3.12"` 1; `python-version-file: .python-version` 1; `ci.yml:23` `pip install uv` 1; `ci.yml:93`
`uv==0.13.6` 1; `ci.yml:127` `"24"` 1; `ci.yml:210` `@redocly/cli` unquoted, quoted and with a
`CI=1` prefix 1 each; `backend/Dockerfile:3` `pip install uv`, `\`-continued `uv`, exec form 1 each,
`uv==0.13.6` 1 (four `ci.yml` lines). Each finding named the mutated file and line. After the last
restore: exit 0. The real repository has no new false positive.

Traceability (CR-005 two-hop scope): 0 errors (see the QA report of this review).

Findings (LOW, not blocking; carried to TASK-213, which changes the same script, test file,
TS-013 1.6 and ADD-024 1.3):

1. **LOW: the `\` join crosses YAML structure in workflows.** `logical_lines`
   (`infra/check_image_pins.py:166-179`) joins any line ending in `\` with the next one, so a step
   line directly after a `run:` block whose last line ends in `\` is swallowed. Reproduced (scratch
   `--root` tree): `echo one \` / `two \` / `- uses: actions/checkout@v4` is not reported. Bash
   accepts the stray `\`, so this is a silent pass the joining introduced. Fix: in workflows, do not
   join into a line that starts a YAML key or list item (`^\s*(-\s+)?[\w-]+:`) or is blank;
   fixture.
2. **LOW: a comment line inside a Dockerfile continuation ends the join.** Docker drops comment
   lines inside a continued instruction; the script appends them, and `PIP_INSTALL` stops at `#`.
   Reproduced: `RUN pip install --no-cache-dir \` / `# the build tool` / `    uv` is not reported.
   Fix: in Dockerfiles, skip comment lines while a continuation is open; fixture.
3. **LOW: the "not seen" list differs in the three places that state it.** Docstring
   (`check_image_pins.py:23-25`: "a multi-line `run:` command assembled by a script file", composite
   actions, `npx` through a script; no anchor, no `pip install uv` through a script), ADD-024
   (lines 46-47: script-file `npx` / `pip install uv`, composite actions; no anchor) and TS-013
   (lines 99-102: script file, YAML anchor or template, composite actions). Fix: one list, the
   TS-013 one plus findings 1-2 if left unfixed, in all three.
4. **LOW: `--root ""` runs the default mode** (`main`: `if args.root` treats the empty string as
   absent), exit 0 on the repository instead of exit 2. Fix: test `args.root is not None`; add the
   case to `test_root_missing_or_without_workflows_or_dockerfiles_exits_2`.

None of the four occurs in the repository; the check passes on it and the negative control holds.

## Version history

- 1.0 (2026-11-12) — Created at the CR-005 Plan stage (Software Architect role); `draft`.
- 1.0 (2026-11-12) — Built (Software Developer role); evidence above; `draft → in_review`. Boxes left unticked for QA.
- 1.1 (2026-11-12) — QA review: CHANGES REQUESTED (1 HIGH, 1 MEDIUM, 4 LOW). `in_review → draft`;
  boxes left unticked; PRB-034 stays `open`.
- 1.2 (2026-11-12) — Round 2 (Software Developer role): QA findings 1-6 addressed (see Round 2); `draft → in_review`. Boxes left unticked for QA; PRB-034 stays `open`.
- 1.3 (2026-11-12) — QA review round 2: APPROVED (4 LOW, carried to TASK-213). `in_review → approved`;
  acceptance-criteria boxes ticked; PRB-034 `open → resolved` (CR-005 AC-11); TS-013 and ADD-024 stay
  `in_review` (TASK-212 and TASK-213 add to TS-013 1.6 and ADD-024 1.3).
