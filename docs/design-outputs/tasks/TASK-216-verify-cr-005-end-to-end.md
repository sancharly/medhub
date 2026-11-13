---
id: "TASK-216"
type: task
title: "Verify CR-005 end to end"
status: approved
version: "1.8"
author: "Carlos Santiago Liceras"
created: "2026-11-12"
updated: "2026-11-13"
links:
  - target: "SR-028"
    relation: implements
  - target: "RISK-010"
    relation: mitigates
  - target: "CR-005"
    relation: relates_to
  - target: "RISK-006"
    relation: relates_to
  - target: "RISK-007"
    relation: relates_to
  - target: "RISK-011"
    relation: relates_to
  - target: "TS-013"
    relation: relates_to
  - target: "TASK-209"
    relation: relates_to
  - target: "TASK-210"
    relation: relates_to
  - target: "TASK-211"
    relation: relates_to
  - target: "TASK-212"
    relation: relates_to
  - target: "TASK-213"
    relation: relates_to
  - target: "TASK-214"
    relation: relates_to
  - target: "TASK-215"
    relation: relates_to
tags: ["verification", "traceability", "cr:CR-005"]
---

# TASK-216 — Verify CR-005 end to end

- **Software items:** all touched by CR-005 (SI-DEVINFRA, SI-DEPLOY, backend tests).
- **CR:** CR-005 (AC-11, AC-12, AC-13; the negative-control criterion as a whole).
- **Depends on:** TASK-209..215, all QA-approved and committed.
- **Branch:** `bug/build-hygiene`.
- **Size:** S (records only: RISK-010, TS-013 environment, CR-005, this task; PLAN-002 if Q-5 is
  answered yes; `docs/design/05-building-blocks.md` only if it describes the CI check's scope).

## Objective

Evidence that the whole change holds on the branch head and on hosted runners, that the records
are complete and traceable, and that the §7.4.3 verification of the affected controls is recorded.

## Steps

1. **Regression (AC-12)** on the branch head:
   - `cd backend && uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=85`;
     `uv run pytest modules/dicom_viewer/tests`;
   - `cd frontend && npm run lint && npm run typecheck && npm test -- --run`;
   - `python3 -m unittest discover -s infra/tests -v`; `python3 infra/check_image_pins.py`;
   - OpenAPI export byte-identical (`uv run python -m app.export_openapi --output openapi/openapi.json && git diff --exit-code`).
2. **Hosted CI (AC-12, needs the human's go-ahead to push):** every job green on the pushed head;
   from the logs record: `Python 3.12.15` in every Python job, `v24.22.2` in every Node job,
   `uv-0.13.7`, the pinned linter version, and each action downloaded at its pinned SHA.
3. **Negative controls (CR-005):** re-run the mutations of TASK-211, TASK-213 and TASK-214 on a
   scratch copy of the head; each check fails as recorded there.
4. **Records (AC-11):** ADD-024 1.3, ADD-026 1.5, SOUP-005 1.3, TS-013 1.6 in review and consistent
   with the code; each PRB has its `## Resolution`; TS-013 environment names the commit tested.
   RISK-010 1.6: replace "planned" in the CR-005 control rows by the evidence; confirm the
   residual 3 × 1 → acceptable. RISK-006, RISK-007 and RISK-011: no change unless the evidence
   contradicts the change analysis (CR-005 "Change analysis").
5. **PLAN-002 (only if Q-5 = yes):** in "SOUP monitoring", one paragraph: the build and CI tool
   pins of SR-028 AC-8 are reviewed with the SOUP list (before every release, at most 365 days
   apart), and a pin is moved only by a reviewed commit. 1.2 → 1.3, `in_review`.
6. **Traceability (AC-13):** `medical-records:traceability-check` over `docs/`: 0 errors for
   CR-005's records (CR-005, SR-028, TASK-209..216, TS-013, ADD-024, ADD-026, SOUP-005, RISK-010,
   PRB-034, PRB-038, PRB-040, PRB-041).

## Acceptance criteria

- [x] CR-005 AC-11: every record above updated and in review; four PRB resolutions written. (QA 2026-11-13:
      records in review, PRB-034/038/040/041 `resolved` with `## Resolution` and an incoming CR-005 `resolves`;
      M-1 below to fix in RISK-010 before the human approves it.)
- [x] CR-005 AC-12: all local suites green (coverage ≥ 85 %); every hosted job green with the
      pinned versions visible in the logs. (QA 2026-11-13: local part re-run and green, see "QA review,
      local part"; hosted run 43385410662 on `a5fd91a`, 8 of 8 jobs green with the pins in the logs, see
      "QA review, hosted part".)
- [x] CR-005 AC-13: `traceability-check` 0 errors for CR-005's records; negative controls re-run. (QA
      2026-11-13: 0 errors, 17 W5; negative controls re-run by QA.)

## Carried from TASK-213 QA (round 2, 2026-11-12)

Non-blocking findings on `infra/check_image_pins.py`, ADR-0020, ADD-024 and TS-013 (details and
reproductions in TASK-213, "QA review round 2"); resolve before CR-005 closes:

- [x] MEDIUM: ADR-0020 dated amendment note under the literal-rule bullet (rule 4, guarantee limited
      to `PostgresContainer` call sites, `DockerContainer` Redis call not checked), README note line
      written (done, see Evidence); the human (Carlos Santiago Liceras) acknowledged it on 2026-11-13.
- [x] LOW 1: definition rebinding by tuple unpacking, `:=`, `for`, `import ... as`, `;` or `globals()`
      is reported (`ast`) or listed under "not seen"; "in any form" wording corrected.
- [x] LOW 2: `PostgresContainer` imported under an alias, and a `POSTGRES_IMAGE` rebinding in a test
      file, are reported or listed under "not seen" (docstring, ADD-024, TS-013).
- [x] LOW 3: ADD-024 and TS-013 "none occurs in the repository" names the `DockerContainer` Redis call
      in `backend/tests/auth/test_session_cap_concurrency.py`.

## Carried from TASK-214 QA (round 2, 2026-11-13)

Non-blocking findings on `infra/tests/test_backend_gunicorn_command.py`, SOUP-005 and PRB-041
(details in TASK-214, "QA review round 2"); resolve before CR-005 closes:

- [x] LOW 1: the forwarded-flag test also catches an abbreviated option name (`--forwarded-allow=*`,
      accepted by Gunicorn's `allow_abbrev=True` parser).
- [x] LOW 2: SOUP-005:80 sentence starts in lower case; its change-log line dates QA round 1 as
      2026-11-13 instead of 2026-11-12.
- [x] LOW 3: PRB-041 Investigation (:31-32) names `--no-control-socket` where it first says "the flag".

## Carried from TASK-215 QA (2026-11-13)

Non-blocking findings (details in TASK-215, "QA review (2026-11-13): APPROVED"); resolve before
CR-005 closes:

- [x] LOW 1: CR-005 AC-9 (:232) "80 checks at HEAD" corrected to 78 for the stack as shipped (two
      more per extra running container; TASK-202's 80 included a scratch `smtp-catcher`), with a
      dated change-log line.
- [x] LOW 2: TASK-215 deviation 2 says the smoke copy differs in 10 lines (it is 9) and does not
      mention the copied untracked `infra/certs/` dev certificate.

## Evidence, local part (Software Developer, 2026-11-13)

Run on `f645979` (branch `bug/build-hygiene`) plus the uncommitted TASK-216 changes. Nothing was
committed, staged or pushed. The developer's MedHub stack (ports 80/443, `infra_*` volumes) was not
touched; the backend suites ran against two throwaway containers on 127.0.0.1:5432 and :6379
(`postgres:16.15@sha256:9e2cf6...` and `redis:7.4.12-bookworm@sha256:b6b6e3...`, the CI service
references), removed afterwards.

**Tools, as the hosted jobs pin them.** Python 3.12.15 (`uv python install`, uv 0.13.7 installed with
`pip install uv==0.13.7` in a scratch venv), Node v24.22.2 (`npm install node@24.22.2` in a scratch
directory; its binary first on `PATH`), `@redocly/cli@2.77.0` through `npx`. Dependencies came from the
frozen lock files into scratch environments (`UV_PROJECT_ENVIRONMENT`, a rsync copy of `frontend/`), so
the developer's `backend/.venv` (Python 3.12.3) and `frontend/node_modules` were not changed.
**Deviation:** `npm` is 9.6.7 (the machine's), not the 10/11 the Node 24 runner bundles; `npm ci` read
`package-lock.json` without change.

| Step (as `.github/workflows/ci.yml`) | Result | Exit |
|---|---|---|
| `uv lock --check` (uv 0.13.7) | `Resolved 86 packages`, lock current | 0 |
| `uv sync --frozen` | Python 3.12.15 environment | 0 |
| `uv run ruff check .` | All checks passed | 0 |
| `uv run black --check .` | 265 files would be left unchanged | 0 |
| `uv run mypy app` | no issues in 133 source files | 0 |
| `alembic upgrade head` (owner role) | to 0010 | 0 |
| `uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=85` | **1549 passed, 6 skipped**, 599 s; coverage **94.51 %** (floor 85 %) | 0 |
| `uv run pytest modules/dicom_viewer/tests` | **25 passed** | 0 |
| `python3 -m unittest discover -s infra/tests -v` | **170 tests OK** (also under Python 3.12.15 and 3.11) | 0 |
| `python3 infra/check_image_pins.py` | no output | 0 |
| `npm ci` / `npm run lint` | 466 packages; ESLint, `--max-warnings 0` clean | 0 / 0 |
| `npm run typecheck` | `tsc --noEmit` clean | 0 |
| `npm test -- --run` | **32 files, 315 tests passed** | 0 |
| `npm run build` | `tsc && vite build`, built in 1.17 s | 0 |
| `app.export_openapi --output <scratch>` vs `backend/openapi/openapi.json` | byte-identical (`cmp`) | 0 |
| `npm run generate:types` on that export vs `frontend/src/api/generated/openapi.ts` | identical (`cmp`) | 0 |
| `npx --yes @redocly/cli@2.77.0 lint` | "Your API description is valid", **9 warnings**, version 2.77.0 | 0 |

The 6 skipped tests are the `object_store` integration tests (they need `OBJECT_STORE_INTEGRATION=1`
and the real store, which the hosted job `object-store-integration` provides; the same skip applies in
the `backend-tests` job). `backend/tests/db/test_postgres_image.py` (TC-013.14, 2 tests) passed:
the started container carries the SOUP-020 digest. The 9 redocly warnings are the count to compare
with hosted run 42779806388 (`operation-4xx-response` and similar, no errors).

**Negative controls re-run (AC-13)** on a scratch git copy of the working tree (`git ls-files -co`),
one mutation at a time, restored after each. Baseline: `check_image_pins.py` exit 0.
`check_image_pins.py` exit 1 at the right file and line for: action by tag `actions/checkout@v4`
(`ci.yml:15`); CI Python 3.12.16 (`ci.yml:20`, differs from `backend/Dockerfile` 3.12.15); one job with
`uv==0.13.8` (`ci.yml:23`); `npx @redocly/cli` without a version (`ci.yml:210`); `node-version: "24"`
(`ci.yml:127`); concatenated `POSTGRES_IMAGE` (`postgres_image.py:12`); indented second assignment
(`:16`); the CI `postgres` service at another tag (`ci.yml:51`); `"postgres:16"` in a test file;
`PostgresContainer()` without an image; and the new forms of this task: `POSTGRES_IMAGE, _X = ...`
(`:15`), `x = 1; POSTGRES_IMAGE = "postgres"` (`:15`), `PostgresContainer` imported `as PC`
(`conftest.py:37`), `POSTGRES_IMAGE = "postgres"` in a test file (`conftest.py:37`). TASK-214 mutants make
`python3 -m unittest discover -s infra/tests -k Gunicorn` fail (exit 1): `--no-control-socket` removed from
the `CMD`; a second `--forwarded-allow=*` (abbreviated); `--forwarded-allow-ips=*`; a `command:` on the
Compose `backend` service.

**Traceability (AC-13).** `medical-records:traceability-check`, fallback parser (no MedTrace run:
the desktop app is not available to the agent), whole `docs/`: 439 records, **0 errors**, 60 warnings
(whole project). CR-005 scope (CR-005, SR-028, TASK-209..216, TS-013, ADD-024, ADD-026, SOUP-005,
RISK-010, PRB-034, PRB-038, PRB-040, PRB-041): **0 errors, 17 warnings**, all W5 (approved element
linking to an `in_review` one): SR-028, TASK-209..214 to RISK-010, ADD-024, ADD-026, TS-013, SOUP-001 and
SOUP-005, which clear when the human approves those records. No W1 (every SR has a TS), no W3, no
unscored RISK, SOUP-005 `anomaly_review` 2026-10-22 (22 days old, limit 365). The report file
`docs/reports/gap-report-2026-11-13.md` was not written (the skill asks for it; left to the
orchestrator's commit decision: the parser output above is the summary).

## Carried findings, how each was handled

- **ADR-0020 MEDIUM.** Dated amendment added under the literal-rule bullet in the style of the 2026-11-12
  notes, with QA's proposed text and the TASK-216 additions, ending "**Amendment pending the human's
  acknowledgement.**"; the same sentence in the Status section; `docs/design/adr/README.md` note line
  extended. No acknowledgement recorded.
- **TASK-213 LOW 1.** Reported, not listed: the definition file is parsed with `ast` (standard library,
  never imported); every `Name` store, `import ... as`, `global` / `nonlocal`, `except ... as` target,
  `:=`, `for`, `with ... as`, `;`-joined statement and every `globals()` / `locals()` / `vars()` call
  after the recognised definition is a "second POSTGRES_IMAGE assignment" (or "namespace access in the
  test image definition"); a definition that does not parse is a finding. "In any form" removed from
  the docstring, ADD-024 and TS-013, which now list the forms.
- **TASK-213 LOW 2.** Reported: `PostgresContainer` imported `as` another name, and any `POSTGRES_IMAGE`
  binding (assignment, `import ... as`, attribute store such as `postgres_image.POSTGRES_IMAGE = ...`) in
  `backend/**/*.py` other than the definition. Still "not seen": `PC = PostgresContainer`, `getattr`,
  `import *`, and a rebinding through `setattr`, `sys.modules` or `vars()` outside the definition file.
  The list is identical in the docstring, ADD-024 and TS-013 (normalised text compared).
- **TASK-213 LOW 3.** The "not seen" sentence in ADD-024, TS-013 and the docstring names the
  `DockerContainer` Redis call in `backend/tests/auth/test_session_cap_concurrency.py` (reads the Compose
  image at run time) and says "none of the others occurs in the repository".
- **TASK-214 LOW 1.** `forwarded_flags()` in `infra/tests/test_backend_gunicorn_command.py` selects every
  argument whose option name is a prefix of `--forwarded-allow-ips` at least `--forwarded` long; new test
  `test_the_flag_check_sees_an_abbreviated_option_name`; the mutant above fails it.
- **TASK-214 LOW 2, LOW 3.** SOUP-005: "The backend image `CMD`" capitalised; the QA round 1 date in the
  2026-11-12 change-log line corrected from 2026-11-13; a dated line added; stays 1.3 `in_review`.
  PRB-041: Investigation says "`--no-control-socket` only skips starting the control server"; 1.5.
- **TASK-215 LOW 1.** CR-005 AC-9 reads "78 checks for the stack as shipped (two more per extra running
  container)"; CR-005 1.4 with a dated history line (wording correction, no scope change).
- **TASK-215 LOW 2.** TASK-215 deviation 2 reads 9 lines and names the copied untracked `infra/certs/`
  dev certificate; TASK-215 1.3, status unchanged (`approved`; wording only, QA may re-check).
- **Q-5 (PLAN-002).** New subsection "Build and CI tool pins" under "SOUP monitoring": pins (actions SHAs,
  CI runtimes, `uv`, `npx` packages, test and CI service images) reviewed with the SOUP list before every
  release and at most 365 days apart, moved only by a reviewed commit. PLAN-002 1.2 → 1.3, `in_review`,
  approval record cleared.
- **Q-6.** ADD-024 already recorded `runs-on: ubuntu-latest` (runner image, Docker, Compose, system `pip`
  and `openssl`) as a documented limit of SR-028 AC-8. RISK-010 named "the hosted runner image" without the
  label; path 3 now says `runs-on: ubuntu-latest` and cites ADD-024. RISK-010 was `approved` at 1.6, so this
  and the evidence change below make it 1.7, `in_review`.
- **RISK-010 control rows.** The three "planned" CR-005 rows now cite the local evidence above (TC-013.11,
  TC-013.12 repository check, TC-013.13, TC-013.14, the re-run negative controls); the hosted-log evidence
  is marked pending. Residual 3 × 1 → `acceptable` unchanged; nothing contradicted the change analysis.
  RISK-006, RISK-007 and RISK-011 not touched.
- **TS-013** environment names the commit of the local run and CI `node-version` 24.22.2; ADD-024 and
  TS-013 version histories note the TASK-216 additions (versions unchanged, as for TASK-213).

## Pending: hosted CI (needs a push, which the human must allow)

- [x] Push the branch (orchestrator asks the human). Every job of the pushed head green. (QA 2026-11-13:
      run 43385410662, head `a5fd91a`, 8 of 8 jobs `success`.)
- [x] From the hosted logs record: `Python 3.12.15` in every Python job; `v24.22.2` in every Node job;
      `uv-0.13.7`; `@redocly/cli` 2.77.0 with the same lint result as run 42779806388 (valid, 9 warnings
      locally); each action downloaded at its pinned SHA (`actions/checkout`, `setup-python`, `setup-node`).
      (QA 2026-11-13: recorded in "QA review, hosted part".)
- [ ] TC-013.12 hosted part, and the RISK-010 control-row text "hosted-log evidence pending": replace by
      the run URL and the head SHA once green; TS-013 environment: add the pushed head.
      (QA 2026-11-13: TS-013 needs no edit. Its environment line and TC-013.12 already say the hosted run
      "is recorded in TASK-216", and it is now recorded there. RISK-010 control row 4 still says
      "pending the push of TASK-216". Not edited: RISK-010 1.7 and TS-013 1.6 carry the human's
      approval of 2026-11-13 with an `approved_digest`, uncommitted in the working tree, and an edit
      would make them "modified after approval". Box open: finding H-1 below, before CR-005 closes.)

## Records awaiting the human's approval at closure

Left `in_review` by CR-005 (the human sets `approved`; nothing was approved by the developer):

| Record | Version | Note |
|---|---|---|
| SOUP-001 Python runtime | 1.3 | TASK-209 |
| SOUP-005 Gunicorn | 1.3 | TASK-214; wording fixes of this task |
| ADD-024 Development and verification infrastructure | 1.3 | TASK-211, 213 |
| ADD-026 Deployment configuration, secrets and runtime users | 1.5 | TASK-210, 214, 215 |
| TS-013 Lifecycle record and traceability verification | 1.6 | TASK-211..213 |
| PLAN-002 Software maintenance plan | 1.3 | new tool-pin paragraph (Q-5) |
| RISK-010 Unreviewed SOUP change | 1.7 | was approved at 1.6; Q-6 text and evidence |
| ADR-0020 amendment (2026-11-12, TASK-213 QA round 2) | n/a | acknowledged by the human 2026-11-13 |

Also for closure, by the roles that own them: TASK-216 (QA, `in_review → approved`), PRB-034, 038, 040
and 041 (`resolved → closed`), CR-005 (`open → closed`), after the hosted run is recorded.
`TASK-215` 1.3 got a wording edit while `approved`; QA may confirm it.

## QA review, local part (2026-11-13): APPROVED-LOCAL

**Verdict:** the local part is approved. No CRITICAL or HIGH finding. One MEDIUM and one LOW are
non-blocking, and both should be fixed **before the push** so the hosted run tests the final head.
The status stays `in_review`: approval waits for the hosted run (below). CR-004's TASK-202 went to
`approved` with its CI box open and a "back to `draft` if the hosted run fails" condition. The
orchestrator asked for `in_review` here, so this task is approved only after the hosted run is
recorded. The carried boxes resolved by the developer are ticked. The ADR-0020 MEDIUM box stays
open for the human's acknowledgement, and so does AC-12 (hosted part).

### Findings

- **M-1 [MEDIUM] RISK-010 control table names the wrong TASKs** —
  `docs/risks/RISK-010-unreviewed-soup-change.md:164-166`, column "Implemented by". The numbers
  are off by one since commit 2f68c42 (TASK-209): the AC-9 "one definition" row says TASK-211, but
  the definition is TASK-212; the "CI rejects" row says TASK-210 and TASK-212, but the check rules
  are TASK-211 (tool rules) and TASK-213 (test image rules); the tools row leaves out TASK-210 (uv).
  The frontmatter `mitigates` links are correct. Only the body is wrong, and 1.7 is the version the
  human approves. → Row 1: `SR-028 AC-8; TASK-209, TASK-210`. Row 2: `SR-028 AC-9; TASK-212`.
  Row 3: `SR-028 AC-8, AC-9; TASK-211, TASK-213 (infra/check_image_pins.py, ADR-0020)`. Add a note
  to the 1.7 history line.
- **L-1 [LOW] the `ast` rule still misses some bindings, and the text says "every"** —
  `infra/check_image_pins.py:393-438` (`_rebinding_findings`). The docstring (:25-26, and "any
  binding" at :42) and ADD-024 say "every later binding", and the ADR-0020 amendment says "every rebinding form is a second
  assignment". QA probes on a fixture tree (`run_images`), and on a scratch copy of the repository
  for `def`, exit 0 for each of these:
  - in the definition file: `def POSTGRES_IMAGE()`, `async def POSTGRES_IMAGE()`,
    `class POSTGRES_IMAGE`, a match capture (`case POSTGRES_IMAGE:`, `[*POSTGRES_IMAGE]`,
    `{**POSTGRES_IMAGE}`), `from os import POSTGRES_IMAGE` and `import POSTGRES_IMAGE` without
    `as`, and `setattr(sys.modules[__name__], "POSTGRES_IMAGE", ...)`. The "not seen" list covers
    `setattr` only "outside the definition file", which implies it is seen inside;
  - in a test file: a parameter `def f(POSTGRES_IMAGE="postgres")`. The docstring says "any
    binding".

  No such code is in the repository.
  → Either report them: the `.name` of `FunctionDef`/`AsyncFunctionDef`/`ClassDef`; `MatchAs` and
  `MatchStar` `.name` and `MatchMapping.rest`; `ast.arg.arg`; in the definition file, an `alias`
  whose bound name (`asname or name.split(".")[0]`) is `POSTGRES_IMAGE`; and `setattr` in the
  namespace-call set. Add one test case per form. Or list them under "not seen" with the same text
  in the docstring, ADD-024 and TS-013, and replace "every". In both cases, correct the ADR-0020
  amendment sentence **before the human acknowledges it**.

### Checked and correct

- **Carried TASK-213 LOW 1-3.** Every form named is reported at the right line, both with the
  one-line and the parenthesised definition: tuple unpacking (both orders), `:=`, `for`,
  `with ... as`, `import ... as`, `;`, `globals()`/`locals()`/`vars()`, `global` in a function,
  `del`, `except ... as`, `type` alias, comprehension target and `sys.modules[...].X =`. A syntax
  error in the definition is reported ("does not parse"). An alias `PostgresContainer as PC`, a
  test-file `POSTGRES_IMAGE` rebinding (module level and inside a function) and an attribute store
  are all reported. `PC = PostgresContainer` and an import from another module are not seen, as
  the list says. The "not seen" text is identical in the docstring, ADD-024 and TS-013
  (normalised, 871 characters each), and it names the `DockerContainer` Redis call
  (`test_session_cap_concurrency.py:48`).
- **No regression of the rule 1 forms.** The HEAD and working scripts give byte-identical output
  and exit code for 16 definition forms: one-line, parenthesised, concatenation, f-string, name,
  no digest, different digest, plain/indented/annotated/augmented/`global` second assignment,
  `OTHER = "postgres:16"`, docstring first, missing, empty. Line numbers are unchanged.
- **Carried TASK-214 LOW 1-3.** The locked Gunicorn 26.0.0 parser accepts `--forwarded=*` and
  `--forwarded-allow=*` (both set `'*'`), and rejects `--forwarde=*` as ambiguous with
  `--forwarder-headers`. So `--forwarded` is the shortest prefix, as the helper assumes. Dockerfile
  mutants on a scratch git copy each fail the `Gunicorn` tests: `--forwarded-allow=*`,
  `--forwarded=*`, `--forwarded-allow-ips=*`, and `--no-control-socket` removed. SOUP-005 and
  PRB-041 wording fixed as claimed.
- **Carried TASK-215 LOW 1-2.** CR-005 AC-9 reads 78, with a 1.4 history line. `smoke-test.sh` has
  9 `https://localhost/` lines. TASK-215 1.3 is a wording-only edit of an approved TASK. TASK
  records here carry no `approved_digest`, and the content matches QA's finding, so QA accepts it
  without re-review.
- **ADR-0020 amendment.** It describes rule 4, limits the guarantee to `PostgresContainer` call
  sites, names the `DockerContainer` Redis call as not checked, and is marked "Amendment pending
  the human's acknowledgement", in the Status section and under the literal-rule bullet. The README
  line says the same. The one overclaim is L-1.
- **PLAN-002 1.3 (Q-5).** It matches the recommended answer the human accepted: reviewed with the
  SOUP list before every release and at most 365 days apart, moved only by a reviewed commit, owner
  named. It also covers the AC-9 test and CI service images, which goes further than the answer and
  is consistent with it. The approval record is cleared and the status is `in_review`. No
  Dependabot or Renovate configuration exists, so "never by automated update tooling" contradicts
  nothing.
- **RISK-010 1.7 (Q-6, residual).** Path 3 names `runs-on: ubuntu-latest` and cites ADD-024. The
  scores are 3 × 1, and `risk_matrix` row 3, column 1 gives `acceptable`, which matches
  `acceptability`. The approval record is cleared, the status is `in_review`, and the "planned"
  rows now cite evidence with the hosted part marked pending. Acceptance is the human's decision.
  The only error is M-1.
- **OpenAPI linter.** Run 42779806388 ran the unpinned `npx --yes @redocly/cli` and printed "valid,
  9 warnings". `@redocly/cli@2.77.0` under Node 24.22.2 on today's export gives "valid, 9
  warnings". The linter prints no version of its own: the version evidence is the `run:` line.

### Verification run (QA, 2026-11-13, `f645979` + the working tree)

| Command | Result |
|---|---|
| `python3 -m unittest discover -s infra/tests -v` (3.15.2; also 3.11 via `uv run --python 3.11`) | 170 tests OK, both |
| `python3 infra/check_image_pins.py` | no output, exit 0 |
| `uvx --from uv==0.13.7 uv lock --check` | uv 0.13.7, `Resolved 86 packages`, exit 0 |
| `ruff check .` / `black --check .` / `mypy app` (backend `.venv`) | all passed / 265 unchanged / no issues in 133 files |
| `pytest modules/dicom_viewer/tests` | 25 passed |
| `alembic upgrade head` (owner role) then `pytest --cov=app --cov-report=term-missing --cov-fail-under=85` (backend `.venv`, Python 3.12.3, CI job env, throwaway `postgres:16.15@sha256:9e2cf6…` and `redis:7.4.12-bookworm@sha256:b6b6e3…`) | to 0010; **1549 passed, 6 skipped** (object-store integration), 594.97 s, coverage **94.51 %**, exit 0 |
| frontend copy, Node v24.22.2, `npm ci` then `lint` / `typecheck` / `test -- --run` | exit 0 / 0 / 0, 32 files, 315 tests passed |
| `app.export_openapi` to scratch vs `backend/openapi/openapi.json`; `generate:types` on it vs `openapi.ts` | both byte-identical (`cmp`) |
| pin-check negative controls (scratch git copy, `git add -A` then reset): `checkout@v4`, a tuple rebinding | exit 1 at `ci.yml:15` and `postgres_image.py:16` |
| `traceability-check` (fallback parser), CR-005 scope (21 records) and one-hop (116) | 0 errors; 17 W5 in scope (as the developer reported), 46 W5 and 6 W6 one-hop; whole `docs/` 439 records, 0 errors |

The throwaway database and Redis for the backend suite ran as `qa216-pg` and `qa216-redis` on
127.0.0.1, and were removed afterwards. The user's `infra` stack was not touched.

### What QA checks in the hosted logs (before `in_review → approved`)

1. The run is on the pushed head SHA. That SHA includes the M-1 and L-1 fixes, and the
   working-tree diff reviewed here, unchanged except for those fixes.
2. Every job is green: the same job set as run 42779806388, plus any job CR-005 added.
3. "Download action repository" lines: `actions/checkout@11d5960a…`, `actions/setup-python@a26af69b…`
   and `actions/setup-node` at the SHAs in `ci.yml`, with no tag resolution.
4. `Successfully set up CPython (3.12.15)` (or the setup-python equivalent) in every Python job.
   `node: v24.22.2` (setup-node "Environment details", or `node --version`) in every Node job.
5. `pip install uv==0.13.7` with `Successfully installed uv-0.13.7` in every job that installs uv.
6. The OpenAPI Lint step's `run:` line shows `npx --yes @redocly/cli@2.77.0 lint openapi.json`, and
   its output says "Your API description is valid" with **9 warnings** (equal to 42779806388).
7. The `image-pins` job runs `check_image_pins.py` and the `infra/tests` unit suite green, and the
   backend job shows the coverage floor met and the DICOM step passed.
8. Then: the TC-013.12 hosted part, the RISK-010 "hosted-log evidence pending" text and the TS-013
   environment take the run URL and head SHA; AC-12 and the pending boxes are ticked; and TASK-216
   moves `in_review → approved`. If any job fails, `in_review → draft` with the failure recorded.

## Follow-up (M-1, L-1) (Software Developer, 2026-11-13)

- **M-1 fixed.** RISK-010 control table "Implemented by": AC-9 "one definition" row TASK-212 (was
  TASK-211); "CI rejects" row TASK-211, TASK-213 (was TASK-210, TASK-212); tools row TASK-209,
  TASK-210 (was TASK-209). The 1.6 history line said "TASK-209..212" and now says "TASK-209..213".
  A note is added to the 1.7 history line. Other TASK numbers in RISK-010 (TASK-215 at 190, the
  older CR-001..003 tasks) match their scopes; the frontmatter has no TASK links. The same
  attribution was checked in CR-005, ADD-024, TS-013, PLAN-002, SOUP-001, SOUP-005, PRB-034,
  PRB-038, PRB-040 and PRB-041: no off-by-one found (209 actions/runtimes/linter, 210 uv, 211 tool
  rules, 212 one definition, 213 test image rules, 214 Gunicorn, 215 fresh volume).
- **L-1 fixed by reporting the forms** (`infra/check_image_pins.py`, `_rebinding_findings`). In the
  definition file: `def` / `async def` / `class` named `POSTGRES_IMAGE`, `match` captures
  (`MatchAs`, `MatchStar` name, `MatchMapping` rest), `import POSTGRES_IMAGE` and
  `from x import POSTGRES_IMAGE` without `as`, and `setattr` added to the namespace-call set. In
  other `backend/**/*.py` files: a function or lambda parameter (`ast.arg`) named
  `POSTGRES_IMAGE`, plus the same def/class/match forms. Tests (one per form, in
  `TestImagesMatchDeployment`): `test_binding_forms_of_the_second_amendment_in_the_definition_file_fail`
  (nine subtests), `test_setattr_in_the_definition_file_fails`,
  `test_function_parameter_named_postgres_image_outside_the_definition_fails` (def, keyword-only,
  lambda), `test_match_capture_outside_the_definition_fails`.
- **"Not seen" list** adjusted identically in the docstring, ADD-024 and TS-013: `setattr`,
  `sys.modules` and `vars()` are not seen in a file other than the definition file; inside it,
  `globals()`, `locals()`, `vars()` and `setattr()` calls are findings. ADD-024 (rule 1 text,
  1.3 history), TS-013 (1.6 history) updated; versions unchanged.
- **ADR-0020 second amendment** reworded so it is true as written (the listed binding forms, not
  "every rebinding form"); still "**Amendment pending the human's acknowledgement.**".
- **Verification.** `python3 -m unittest discover -s infra/tests -v`: 174 tests OK (170 before),
  also under python3.11 (174 OK); `python3 infra/check_image_pins.py` exit 0, no output; the QA
  regress script (HEAD against the tree, 16 rule 1 definition forms) gives identical output and
  exit codes. `graphify update .` run.

## QA review, hosted part (2026-11-13): APPROVED

**Verdict:** APPROVED. Hosted CI run
[43385410662](https://github.com/sancharly/medhub/actions/runs/43385410662) (workflow CI, event
`push`, branch `bug/build-hygiene`) ran on head `a5fd91aaa0020f4c5c945ba84f6debd5cf2923e1`, which
is the branch tip on `origin`. All 8 jobs concluded `success`. Every item of "What QA checks in
the hosted logs" holds. AC-12 is met, and TASK-216 goes `in_review → approved`.

The ADR-0020 MEDIUM box stays open for the human's acknowledgement. It does not block this
approval: the carried section says to resolve those findings "before CR-005 closes", not before
this task is approved. The same applies to H-1.

### Findings

- **H-1 [LOW] RISK-010 still says the hosted evidence is pending** —
  `docs/risks/RISK-010-unreviewed-soup-change.md:168`, control row "Every tool that builds the
  images or runs CI pinned", column "Verified by". The row says "hosted CI logs (Python 3.12.15,
  Node v24.22.2, uv 0.13.7, redocly 2.77.0): pending the push of TASK-216" and "170 infra unit tests
  OK" (174 at `a5fd91a`). The record is approved at 1.7 in the working tree, so QA did not edit it.
  → Before CR-005 closes, with the human's agreement, replace the row text with "TC-013.11 (174
  infra unit tests OK, local and hosted); TC-013.12 (`python3 infra/check_image_pins.py` exit 0,
  local and hosted); hosted CI run 43385410662 on `a5fd91a` (Python 3.12.15, Node v24.22.2,
  uv 0.13.7, `@redocly/cli@2.77.0`, actions at their pinned SHAs; TASK-216 QA, hosted part)". Then
  add a 1.7 history line and have the human approve again. The residual 3 × 1 → `acceptable` is
  not affected.

### Checklist evidence (hosted log, `gh run view 43385410662 --log`)

| # | Check | Evidence | Result |
|---|---|---|---|
| 1 | Head SHA | `headSha` a5fd91aaa0020f4c5c945ba84f6debd5cf2923e1. Every job's checkout runs `fetch ... origin +a5fd91aaa0020f4c5c945ba84f6debd5cf2923e1:refs/remotes/origin/bug/build-hygiene`. `git ls-remote origin bug/build-hygiene` gives the same SHA. `a5fd91a` contains M-1 and L-1 (`git show --stat`) | holds |
| 2 | Every job green | Backend Quality, Image Pin Check, Docker Build, Frontend Quality, Frontend Tests, Backend Tests, Object Store Integration and OpenAPI Lint: all `success`, and no step failed. This is the same 8-job set as run 42779806388 | holds |
| 3 | Actions at the `ci.yml` SHAs | 15 "Download action repository" lines. `actions/checkout@11d5960a326750d5838078e36cf38b85af677262` appears in all 8 jobs. `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065` appears in Backend Quality, Backend Tests, Object Store Integration and OpenAPI Lint. `actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020` appears in Frontend Quality, Frontend Tests and OpenAPI Lint. Each line shows `(SHA:<same>)`, so no tag was resolved | holds |
| 4a | CPython 3.12.15 | "Successfully set up CPython (3.12.15)" appears in the 4 Python jobs, followed by `uv sync` "Using CPython 3.12.15 interpreter at: /opt/hostedtoolcache/Python/3.12.15/x64/bin/python3". The image builds (Docker Build, and the object store's backend build) use `/usr/local/bin/python3` 3.12.15 | holds |
| 4b | Node v24.22.2 | "node: v24.22.2" appears in the 3 Node jobs (Frontend Quality, Frontend Tests, OpenAPI Lint) | holds |
| 5 | uv 0.13.7 | `Run pip install uv==0.13.7`, then "Successfully installed uv-0.13.7", in the 4 jobs that install uv. The two image builds also print it (Docker Build backend image, Object Store Integration). 6 occurrences in total, and no other uv version anywhere | holds |
| 6 | Linter pin and result | `Run npx --yes @redocly/cli@2.77.0 lint openapi.json`, then "Woohoo! Your API description is valid." and "You have 9 warnings." (`info-license` and `operation-4xx-response`). Run 42779806388 also gave valid with 9 warnings | holds |
| 7a | Pin check job | `python3 -m unittest discover -s infra/tests -v`: "Ran 174 tests", "OK". This includes the L-1 tests `test_binding_forms_of_the_second_amendment_in_the_definition_file_fail`, `test_setattr_in_the_definition_file_fails`, `test_function_parameter_named_postgres_image_outside_the_definition_fails` and `test_match_capture_outside_the_definition_fails`. `python3 infra/check_image_pins.py` printed nothing and the step succeeded | holds |
| 7b | Backend coverage and DICOM | "1549 passed, 6 skipped" and "Required test coverage of 85% reached. Total coverage: 94.51%". "Run DICOM viewer module tests": "25 passed". The 6 skipped tests are the ones Object Store Integration runs ("6 passed, 1549 deselected") | holds |
| AC-7 (hosted) | Test PostgreSQL image | The Backend Tests service container shows `docker pull postgres:16.15@sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97`, "Digest: sha256:9e2cf6…0a97". This equals `backend/postgres_image.py` and `infra/docker-compose.yml:126`. Redis is `redis:7.4.12-bookworm@sha256:b6b6e3…82f5`. Testcontainers pulls are not logged; `tests/db/test_postgres_image.py` is among the 1549 passed | holds |
| Other | Quality and frontend | `uv lock --check` "Resolved 86 packages". Ruff "All checks passed!". Black "265 files would be left unchanged.". Mypy "no issues found in 133 source files". Vitest "32 passed (32)" files and "315 passed (315)" tests | holds |

**Observation (not a finding).** Each job ends with "Node.js 20 is deprecated. The following actions
target Node.js 20 but are being forced to run on Node.js 24", naming the pinned
checkout, setup-python and setup-node v4.4.0/v5.6.0. The actions ran and passed. A later SOUP or
tool-pin review under PLAN-002 Q-5 should consider moving to releases that target Node 24.

### M-1 / L-1 follow-up spot-check (`a5fd91a`)

- M-1: RISK-010:168-170 "Implemented by" now reads TASK-209, TASK-210 / TASK-212 / TASK-211,
  TASK-213, and the 1.7 history line notes the correction.
- L-1: `python3 -m unittest discover -s infra/tests` gives 174 tests OK locally (and the same 174
  hosted). `python3 infra/check_image_pins.py` exits 0. The new tests cover each probe form of L-1:
  def, async def, class, the four match forms, bare `import` and `from x import`, `setattr`, and
  def, keyword-only and lambda parameters.
- ADR-0020's second amendment now names "the binding forms listed in ADD-024", not "every
  rebinding form", so it is true as written. It ends "**Amendment pending the human's
  acknowledgement.**", and the README line says it is pending.

### Records state seen at this review

The working tree is uncommitted, and nothing there was changed by QA. It shows SOUP-001 1.3,
SOUP-005 1.3, ADD-024 1.3, ADD-026 1.5, TS-013 1.6, PLAN-002 1.3 and RISK-010 1.7 as `approved` on
2026-11-13 by the human. Each has an `approved_digest`, with `approval_note: self-approved`, and
`docs/medtrace.yml` has `allow_self_approval: true`. QA did not change their status or content. These
approvals are not in `a5fd91a`: the orchestrator's commit carries them.

### Traceability (`medical-records:traceability-check`, fallback parser, after this edit)

The CR-005 scope is CR-005, SR-028, TASK-209..216, TS-013, ADD-024, ADD-026, SOUP-001, SOUP-005,
RISK-010, PLAN-002, PRB-034, PRB-038, PRB-040 and PRB-041 (21 records). It has **0 errors and 0
warnings**. The 17 W5 of the local review are cleared by the working-tree approvals. Across the
whole of `docs/` (439 records) there are 0 errors and 11 warnings, all outside the scope and from
before CR-005: W1 SR-017, SR-018, SR-026; W5 TASK-132, TASK-142 → TASK-101 and TASK-202 →
TASK-113; W6 TASK-165, 175, 176 and CR-002 → obsolete SOUP. No MedTrace run was made, because the
desktop app is not available to the agent. `approved_digest` is not recomputed by the fallback.

## Version history

- 1.0 (2026-11-12) — Created at the CR-005 Plan stage (Software Architect role); `draft`.
- 1.1 (2026-11-12) — QA (TASK-213 round 2): one MEDIUM and three LOW findings carried; `draft` unchanged.
- 1.2 (2026-11-13) — Orchestrator: three LOW findings carried from TASK-214 QA round 2; `draft` unchanged.
- 1.3 (2026-11-13) — Orchestrator: two LOW findings carried from TASK-215 QA; `draft` unchanged.
- 1.4 (2026-11-13) — Local part built (Software Developer role): carried findings handled, Q-5 and Q-6 recorded, local suites and negative controls run, traceability summarised; the hosted-CI part stays pending. `draft → in_review`. Boxes left unticked for QA.
- 1.5 (2026-11-13) — QA review, local part: APPROVED-LOCAL (1 MEDIUM, 1 LOW, non-blocking, to fix before the push). AC-11, AC-13 and the carried boxes the developer resolved are ticked; the ADR-0020 acknowledgement, AC-12 and the hosted-CI boxes stay open. Status stays `in_review` until the hosted run is recorded.
- 1.6 (2026-11-13) — Follow-up to the QA review, local part: M-1 (RISK-010 task attribution) and L-1 (`ast` rule forms, "not seen" list, ADR-0020 wording) fixed. Status stays `in_review`.
- 1.7 (2026-11-13) — QA review, hosted part: APPROVED on run 43385410662 (head `a5fd91a`, 8 of 8 jobs green, pins visible in the logs). AC-12 and the hosted boxes are ticked. The RISK-010 hosted-evidence row is left open as H-1 (LOW, the record is human-approved). The ADR-0020 acknowledgement is still pending (before CR-005 closes). `in_review → approved`.
- 1.8 (2026-11-13) — Orchestrator: the human acknowledged the second ADR-0020 amendment (box ticked) and approved SOUP-001 1.3, SOUP-005 1.3, ADD-024 1.3, ADD-026 1.5, TS-013 1.6, PLAN-002 1.3 and RISK-010 1.7 in MedTrace. H-1 (RISK-010 hosted-evidence cell) stays open before CR-005 closes. Status stays `approved`.
