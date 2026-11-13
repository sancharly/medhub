# ADR-0020: Tool and test-image pins are enforced by the existing pin check, against the shipped references

## Status

Accepted (2026-11-12, Carlos Santiago Liceras, CR-005 plan gate). Proposed the same day at the
CR-005 Plan stage by the Software Architect role.

Amended 2026-11-12 (TASK-212 QA review, findings 1 and 2; Software Architect role): the location
of the test definition and the form the script reads. **The human (Carlos Santiago Liceras)
acknowledged the amendment on 2026-11-12.** The decision (option 1, sources of truth, rule families) is unchanged; see the
dated notes in the Decision.

Amended 2026-11-12 (TASK-213 QA round 2): the test-container rule (rule 4) and the limit of its
guarantee. **The human (Carlos Santiago Liceras) acknowledged the amendment on 2026-11-13.**

## Context

SR-028 1.7 adds AC-8 (every tool that builds the images or runs CI has an exact version: actions by
40-hex commit SHA, CI Python and Node.js at the patch version of the matching base image, one exact
`uv` version) and AC-9 (every test that starts a SOUP component as a container uses the
deployment's image reference). Both say that CI fails, naming file and line, on a reference that
breaks them (PRB-034, PRB-040).

The repository already has one such check: `infra/check_image_pins.py` (CR-001 TASK-156, ADD-024
`U-INF-CIPipeline`), standard library only, line-based, run by the CI job "Image Pin Check" after
its unit tests (`infra/tests/test_check_image_pins.py`, TS-013 TC-013.5, TC-013.6). It checks
container image references for a digest, one file at a time. It does not read Python test code and
does not compare references across files.

The hosted run of 2026-11-10 shows the gap: CI ran Python 3.12.16 and uv 0.13.7, while the image
ships Python 3.12.15 (SOUP-001) and installs whichever uv is newest at build time. The OpenAPI
lint step also runs `npx --yes @redocly/cli` with no version, which PRB-034 did not list.

## Options

1. **Extend `infra/check_image_pins.py`** with rule families for tool references and cross-file
   equality rules, keeping its form (standard library, line-based, file and line per finding) and
   its CI job.
2. **A second script** beside it, with its own CI step and tests.
3. **A third-party workflow linter** (for example pinact, ratchet or zizmor).
4. **No test-image definition to compare:** the test helper reads the image from
   `infra/docker-compose.yml` at test time, so the two cannot differ.

## Decision

Option 1.

- **Rule families added to the script.** Each prints `<path>:<line>: <message>: <reference>` and
  makes the exit code 1; the existing image message and exit codes are unchanged, so TC-013.5 and
  TC-013.6 keep passing as written.
  - Workflow `uses:` of a repository action must name a 40-hex commit SHA followed by a comment
    naming the release tag (`# vX.Y.Z`). `uses: ./…` (local) is exempt; `docker://…` is checked
    by the image rule.
  - Workflow `python-version` and `node-version` must be `X.Y.Z` and equal the source of truth
    below.
  - A `uv` install in a workflow `run:` or a Dockerfile `RUN` must be `uv==X.Y.Z`, and every such
    version in the repository must be the same.
  - A workflow `npx` call must name its package with an exact version (`pkg@X.Y.Z`).
  - Every workflow `services.<name>.image` of a SOUP component, and the test definition
    `POSTGRES_IMAGE` in `backend/postgres_image.py`, must equal, character for character,
    the `image:` of the Compose service that runs the same image repository in
    `infra/docker-compose.yml` (tag and digest).
    > Amended 2026-11-12 (TASK-212 QA finding 1): the path read `backend/tests/postgres_image.py`.
    > See "Test definition beside the test roots" below.
  - A string literal naming the image repository of a Compose service (`"postgres:…"`) in
    `backend/**/*.py` outside the test definition is a finding, so a new call site cannot bring a
    floating tag back (the way PRB-040 grew from two call sites to eleven).
    > Amended 2026-11-12 (TASK-213 QA round 2; Software Developer role, TASK-216, 2026-11-13): the
    > literal rule alone does not stop a call with no literal (`PostgresContainer()` defaults to
    > `postgres:latest`). A fourth rule makes every `PostgresContainer(` call in `backend/**/*.py` take
    > `POSTGRES_IMAGE` as its image; the guarantee covers `PostgresContainer` call sites. Other
    > container classes (`DockerContainer`, used for Redis in
    > `tests/auth/test_session_cap_concurrency.py`) are not checked. TASK-216 adds that a
    > `PostgresContainer` imported under an alias, and a `POSTGRES_IMAGE` binding outside the
    > definition file, are findings, and that the files are read with `ast`: in the definition file the
    > binding forms listed in ADD-024 (assignment forms, `import`, `def`, `class`, `match` captures,
    > `global`, and `globals()` / `locals()` / `vars()` / `setattr()` calls) are a second assignment; in
    > another `backend/**/*.py` file the same bindings, a function parameter and an attribute store are
    > findings. Forms the script does not see are listed under "not seen" in ADD-024. **The human (Carlos Santiago Liceras) acknowledged the amendment on 2026-11-13.**
- **Sources of truth** are the shipped references, never a second list: the CI Python version is
  the tag version of `FROM python:X.Y.Z-…` in `backend/Dockerfile` (equal to SOUP-001
  `soup_version`); the CI Node.js version is the tag version of `FROM node:X.Y.Z-…` in
  `frontend/Dockerfile`; the test PostgreSQL image is the Compose `postgres` image (equal to
  SOUP-020). The `uv` version has no shipped counterpart; the rule is that all occurrences agree.
- **Reading files.** The script reads the test definition as text, never by importing backend
  code, so the "Image Pin Check" job keeps needing only Python 3 and `git`. It accepts exactly one
  assignment to `POSTGRES_IMAGE`, at the start of a line, in one of two forms: one line
  `POSTGRES_IMAGE = "<ref>"`, or the parenthesised form `black` writes when that line is too long
  (`POSTGRES_IMAGE = (`, one line holding a single string literal, a line holding `)`). The value is
  one plain string literal, single or double quoted: no implicit or `+` concatenation, no f-string,
  prefix or name, nothing else on those lines. Any other form, or a second assignment, is a finding
  at its line; a finding names the line of the literal.
  > Amended 2026-11-12 (TASK-212 QA finding 2): this read "(one assignment line)". The one-line form
  > of the pinned reference is 105 characters and fails `ruff` E501 (limit 100), so `black` and the
  > source use the parenthesised form. Reading that form was chosen over a one-line assignment with
  > `# noqa: E501`: the script then accepts the form the formatter produces, needs no lint
  > suppression, and still reports every form it does not recognise rather than passing it.
- **Cross-file rules and fixtures.** The cross-file rules run over a repository root: by default
  the git repository (tracked files, fixtures excluded, as today); the unit tests point the script
  at small fixture trees under `infra/tests/fixtures/`. The per-file image mode with explicit paths
  stays as it is.
- **Test definition beside the test roots.** `backend/postgres_image.py` holds the one constant.
  Both test roots import it as `from postgres_image import POSTGRES_IMAGE` (`backend/` is on
  `sys.path` for `tests/` and for `modules/dicom_viewer/tests/`). It is test code and never ships:
  `backend/Dockerfile` copies only named files and directories, and coverage measures `app` only.
  > Amended 2026-11-12 (TASK-212 QA finding 1): this read "Test definition in the test tree.
  > `backend/tests/postgres_image.py` holds the one constant." That module cannot be imported from
  > the DICOM suite: `backend/modules/dicom_viewer/tests/__init__.py` makes `tests` resolve to the
  > DICOM package, so `from tests.postgres_image import …` fails there with `ModuleNotFoundError`
  > (shown by QA on a scratch copy).

Option 2 was rejected: two scripts would share the file walk, the output form and the fixtures,
and a second CI step would duplicate the job. Option 3 was rejected: it adds a tool that must itself
be pinned and reviewed, needs the network or a container, and does not know MedHub's sources of
truth (the base images and Compose). Option 4 was rejected: the backend tests would parse a file
of another software item at run time, and SR-028 AC-9 and CR-005 AC-5, AC-6 ask for one definition
plus a CI check; the check also covers the CI service containers, which option 4 cannot reach.

## Consequences

### Positive

- One check, one CI job and one test suite keep every pinned reference: shipped images (AC-5),
  build and CI tools (AC-8), test containers (AC-9).
- A version change of Python, Node.js or PostgreSQL needs one edit at the shipped reference; CI
  then names every place that still differs.

### Negative

- The script grows from one rule to several and is still line-based. Forms it does not parse (a
  multi-line `uses:` or `python-version` from an expression) are reported as findings, never
  passed: a false positive blocks a merge, a false negative would not be seen. The fixtures
  include such forms.
- The hosted runner image (operating system, Docker, Compose, the system `pip` and `openssl`) is
  outside any repository pin (CR-005 Q-6).

### Neutral

- Exact pins do not update themselves. Moving any pin is a reviewed change (PLAN-002 cadence;
  CR-005 Q-5).

## References

- Requirements: SR-028 AC-5, AC-8, AC-9; RR-008, RR-010
- Problem reports: PRB-034, PRB-040
- Risks: RISK-010 (and the verification evidence of RISK-006, RISK-011)
- SOUP: SOUP-001 (Python), SOUP-020 (PostgreSQL), SOUP-021 (Redis)
- Related: ADD-024 `U-INF-CIPipeline`; TS-013; CR-001 TASK-156; CR-005 TASK-209..212
