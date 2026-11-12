---
id: CR-005
type: change-request
title: Make the build, test and deployment configuration reproducible
status: open
version: "1.4"
author: Carlos Santiago Liceras
created: "2026-11-12"
updated: "2026-11-13"
branch: bug/build-hygiene
risk_impact: affects_controls
links:
  - target: PRB-034
    relation: resolves
  - target: PRB-038
    relation: resolves
  - target: PRB-040
    relation: resolves
  - target: PRB-041
    relation: resolves
  - target: SR-028
    relation: relates_to
  - target: SR-041
    relation: relates_to
  - target: RR-010
    relation: relates_to
  - target: RR-008
    relation: relates_to
  - target: ADD-024
    relation: relates_to
  - target: ADD-026
    relation: relates_to
  - target: SOUP-001
    relation: relates_to
  - target: SOUP-005
    relation: relates_to
  - target: SOUP-020
    relation: relates_to
  - target: RISK-006
    relation: relates_to
  - target: RISK-007
    relation: relates_to
  - target: RISK-010
    relation: relates_to
  - target: TS-013
    relation: relates_to
  - target: RISK-001
    relation: relates_to
  - target: RISK-011
    relation: relates_to
  - target: SOUP-021
    relation: relates_to
  - target: TASK-209
    relation: relates_to
  - target: TASK-210
    relation: relates_to
  - target: TASK-211
    relation: relates_to
  - target: TASK-212
    relation: relates_to
  - target: TASK-213
    relation: relates_to
  - target: TASK-214
    relation: relates_to
  - target: TASK-215
    relation: relates_to
  - target: TASK-216
    relation: relates_to
tags:
  - configuration-management
  - reproducibility
  - class:B
  - issue:sancharly/medhub#34
---

# CR-005 — Make the build, test and deployment configuration reproducible

## Reason

The release gate of PLAN-001 and RR-010 ask for a build that can be reproduced from
version-controlled sources (IEC 62304 §5.8.5, §8.1). They also ask for verification evidence that
applies to the shipped versions (§8.1.2, CR-001 A-2). CR-001 pinned everything that ships. Four
`minor` problem reports raised during CR-001 are still open. Each leaves a moving part or known
noise in the build, test or deployment configuration:

- **PRB-034:** the tools that build and verify MedHub are referenced by floating versions. GitHub
  Actions use a major tag in all eight CI jobs, CI installs Python `3.12` and Node.js `24` without
  a patch version, and `pip install uv` has no version in `backend/Dockerfile` and in four CI jobs.
  Two builds of one commit can use different tools.
- **PRB-040:** nine real-database and migration test call sites start `postgres:16`, not the
  SOUP-020 reference `postgres:16.15@sha256:9e2cf628…`. Since CR-004 that includes the evidence for
  the audit log's append-only grants (RISK-006) and the key-identifier migration (RISK-011).
- **PRB-038:** `POSTGRES_PASSWORD` was missing from the environment template. CR-004 TASK-203
  fixed this as a side effect, but no CR resolves the PRB, and no fresh-volume bring-up has been
  recorded against it.
- **PRB-041:** Gunicorn's control server fails with `Permission denied: '/home/medhub'` on every
  backend start. The interface it would open is unused. An ERROR line on every normal start
  trains operators to ignore backend errors, and the log monitoring behind RISK-007 depends on
  those errors.

One CR bundles them, as CR-001 did, because they come from the same review, share one record set
(SR-028, ADD-024, ADD-026, TS-013) and one verification run: full CI on hosted runners, a
fresh-volume started stack and `traceability-check`. PRB-007 (#27) is closed with CR-004, so no
coordination is needed.

Source: GitHub issue sancharly/medhub#34.

## Scope

### In scope

| PRB | Crit. | Requirement restored (AC) | Change |
|---|---|---|---|
| PRB-034 Floating CI and image-build tooling | minor | **SR-028 AC-8 (new in 1.7)**; RR-010 | Pin every GitHub Action by full commit SHA (release tag in a comment). Set full patch versions for CI Python and Node.js, equal to the base images. Pin one exact `uv` version in `backend/Dockerfile` and in every CI job. Add a CI check that refuses a floating reference of any of these. |
| PRB-040 DB tests use a floating PostgreSQL tag | minor | **SR-028 AC-9 (new in 1.7)**; RR-008 | Start every test PostgreSQL from the SOUP-020 reference (tag and digest), taken from one definition in the test code. Add a CI check that the definition equals the Compose `postgres` image. |
| PRB-038 `POSTGRES_PASSWORD` missing from the template | minor | SR-041 AC 2, AC 4 (already met at HEAD) | No code change is expected. Verification only: a fresh-volume bring-up from the template (Q-1). |
| PRB-041 Gunicorn control server fails at every start | minor | none (operational hygiene; RISK-007 log signal) | Disable the unused control socket with `--no-control-socket` on the Gunicorn command in the `backend/Dockerfile` `CMD`. Since TASK-191 that is where the command lives, not `backend/entrypoint.sh`. Record the configuration in SOUP-005 and ADD-026. |

Records: ADD-024 (`U-INF-CIPipeline`: the tooling pins and the extended check), ADD-026 (the
Gunicorn command), SOUP-005 (control socket disabled by configuration), TS-013 (test cases for
SR-028 AC-8 and AC-9), and each PRB's `## Resolution`. The Software Architect creates the TASKs at
the Plan stage.

### Requirements decision

- **SR-028 amended (1.6 → 1.7, `in_review`, approval record cleared).** RR-010 asks for a
  reproducible build, but SR-028 AC-5 covers only components that ship or are needed at runtime.
  The CI tooling and the test container are neither, so PRB-034 and PRB-040 had no testable
  criterion. SR-028 gains:
  - **AC-8:** every tool that builds the images or runs CI has an exact version. Actions are
    pinned by commit SHA, CI runtimes by a patch version equal to the base images, and the package
    manager by one exact version. CI fails on a floating reference.
  - **AC-9:** test containers of SOUP components use the deployment's image reference, and CI
    fails when they differ.

  Amending was preferred to a new SR because SR-028 already carries the whole trace: it
  `satisfies` RR-008 and RR-010, `mitigates` RISK-010, and is covered by ADD-024. CR-001 and
  CR-002 set the same precedent.
- **SR-041 unchanged.** Its AC 2 and AC 4 already state what PRB-038 asked for, and the tree meets
  them (PRB-038 Investigation).
- **No SR for PRB-041.** No requirement states that the backend log is free of errors at
  start-up, and none is proposed. The fix removes an unused, default-on management interface and
  a false error signal, as PRB-067 did in CR-004 without an SR criterion. AC-8 below checks it
  directly.
- **No new UN, NFR or RR.** RR-008 and RR-010 already cite the clauses.
- **§5.2.2 walk (SR-028 1.7):** a (capability), c (interfaces: GitHub Actions, the package
  registry) and h (installation: a reproducible image build) apply and are covered by AC-8 and
  AC-9. l (regulatory) is RR-010. b, d, e, f, g, i, j and k do not apply: no input, alarm, security
  function, user interaction, data definition, operation method, network aspect or user
  documentation changes. The tool pins narrow the supply-chain surface of the build without being
  a security function of the product.

### Out of scope

- Upgrading any SOUP item, or any tool to a newer minor or major version. Pinning records the
  version in use when the pin is made.
- `init: true` for the backend service (Q-3). SOUP-005 judges the PID-1 reaping bug (#3220)
  availability-only, with no trigger in MedHub, and Gunicorn 26.1.0 fixes it.
- Automated update tooling for the pins (Dependabot, Renovate). The PLAN-002 review cadence applies.
- `.pre-commit-config.yaml` hook revisions. They are developer tooling, and CI does not run them.
- The testcontainers reaper image. The locked `testcontainers` version selects it, and it is not
  SOUP.
- PRB-072 (the single API worker killed under parallel writes). It touches Gunicorn, but its cause
  and fix are different.
- Changing a PRB to `resolved` or `closed`, or any record to `approved`. Only QA and the human do
  that.

### Boundaries

- **Ask first:** a change of version (not only a pin) for any tool or image; any change to what
  the backend image contains beyond the Gunicorn flag (AC-10).
- **Never:** edit an installed plugin copy; set a record `approved`; let a check pass by
  excluding a real reference from its scope.

### Risk impact (§7.4)

Preliminary classification: **`affects_controls`**. SR-028 is a design and protective control of
RISK-010 (unreviewed SOUP change), and AC-8 and AC-9 extend it from the shipped components to the
tools and test containers that produce the verification evidence. The tests now run against the
shipped PostgreSQL version, which strengthens the verification of the RISK-006 and RISK-011
controls. Removing the start-up ERROR line restores the error signal of the backend log, on which
RISK-007's monitoring relies. No new hazard is expected and class B is unchanged.

Two risks introduced by the change, for the Risk stage:

- Pinned actions and tools no longer pick up upstream security fixes on their own. The PLAN-002
  cadence is the counterweight, as RISK-010 already records for images.
- A wrong uv pin or a wrong Gunicorn flag could change the image. AC-10 compares the installed set
  before and after the change, and AC-8 checks the start-up.

The Risk stage confirms or revises the classification and records the §7.4.1–7.4.3 analysis in
this CR.

## Verification approach

IEC 62304 §8.2.1 (change approval), §8.2.3 (verification of changes) and §7.4.3 (verification of
risk-control measures after a change). Every criterion is checked on the branch head.

- **AC-1 (PRB-034, SR-028 AC-8).** Every `uses:` that references a repository action in
  `.github/workflows/*.yml` names a full 40-hex commit SHA, with the release tag in a trailing
  comment. For each SHA, the developer confirms against the action's repository that it is the
  commit of the named tag, and records the check in the TASK.
- **AC-2 (PRB-034, SR-028 AC-8).** Every `python-version` in CI is `3.12.15`, which equals SOUP-001
  `soup_version` and the `backend/Dockerfile` base image tag. Every `node-version` equals the
  Node.js version of the `frontend/Dockerfile` build image tag (`24.22.2` at HEAD).
- **AC-3 (PRB-034, SR-028 AC-8).** `uv` is installed with one exact version (`uv==X.Y.Z`) in
  `backend/Dockerfile` and in every CI job that installs it (four at HEAD), and it is the same
  version everywhere. `uv lock --check` passes with that version.
- **AC-4 (PRB-034, SR-028 AC-8).** A CI check fails, naming file and line, on each of these: an
  action reference without a 40-hex SHA, a `python-version` or `node-version` without a patch
  version, and a `uv` install without an exact version. Unit tests show one passing and one
  failing fixture for each form. The check passes on the repository. Recorded as new TS-013 test
  cases.
- **AC-5 (PRB-040, SR-028 AC-9).** Every test that starts PostgreSQL through testcontainers (nine
  call sites at HEAD) uses `postgres:16.15@sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97`
  from one definition. A search of `backend/` for a `postgres:` image string outside that
  definition finds nothing.
- **AC-6 (PRB-040, SR-028 AC-9).** A CI check fails, naming file and line, when the test definition
  differs from the `postgres` service `image:` in `infra/docker-compose.yml` or has no digest. Unit
  tests show one passing and one failing fixture for each case. Recorded as a TS-013 test case.
- **AC-7 (PRB-040).** The real-database and migration tests pass in CI and locally, and the image
  of a container the tests start is shown to carry the SOUP-020 digest. Evidence, for example
  `docker inspect` of the started container, is recorded in the TASK.
- **AC-8 (PRB-041).** The backend's Gunicorn command includes `--no-control-socket`, and an infra
  test checks this on the image configuration. On a started stack, the backend log from start-up
  through the first served request has no `Control server error` line and no Gunicorn `[ERROR]`
  line, and a login through the reverse proxy is answered.
- **AC-9 (PRB-038).** Fresh-volume bring-up: a new Compose project with no existing volumes, and
  an `infra/.env` built from `infra/.env.example` with only the required secret values filled
  (generated). `docker compose up -d --build --wait` succeeds, PostgreSQL initialises with
  `POSTGRES_PASSWORD`, `db-migrate` completes, and `infra/smoke-test.sh` reports every check
  passed and 0 failed. At HEAD that is 78 checks for the stack as shipped (two more per extra
  running container). The issue's "17/17" dates from CR-001. The same
  `.env` with `POSTGRES_PASSWORD` empty stops Compose with `POSTGRES_PASSWORD must be set`. The
  run is torn down with `down -v`, and the developer's own volumes are untouched.
- **AC-10 (PRB-034, §7.4).** For the same `backend/uv.lock`, the backend image built after the
  change contains exactly the same Python distributions and versions as the image built before it
  (a frozen list from `/app/.venv`, compared).
- **AC-11 (records).** SR-028 1.7 is approved by the human before the Plan stage. The §7.4
  change analysis is recorded in this CR. ADD-024, ADD-026, SOUP-005 and TS-013 are updated. Each
  of PRB-034, PRB-038, PRB-040 and PRB-041 has its `## Resolution` written and moves to `resolved`
  only after QA approves its TASK.
- **AC-12 (regression).** The full suites pass on the branch head: backend with the coverage floor
  of 85%, the DICOM module, frontend, the infra unit tests, and every job of the CI pipeline on
  hosted runners with the new pins.
- **AC-13 (traceability).** `traceability-check` reports 0 errors for CR-005's records.
- **Negative control.** For each new check (AC-4, AC-6, AC-8's infra test), reverting the pin or
  the flag makes it fail.

Results go into the next test report (TR) for the release.

## Assumptions

- **A-1:** No release exists (`docs/releases/` is absent), so no released version in use is
  affected and no notification is needed (§9.3).
- **A-2:** This CR's `status` is `open`. The hand-off asked for `draft`/`in_review`, but those
  values are not in the change-request status set (`open`, `in_progress`, `closed`, `rejected`).
  The human's approval at the Specify gate is recorded as a decision in this record, as in CR-001
  to CR-004.
- **A-3:** `actions/setup-python` can install Python 3.12.15 on the hosted runner. If it cannot,
  the architect proposes another way to get the same patch version (for example `uv python
  install`). AC-2 does not change.
- **A-4:** Gunicorn 26.0.0 accepts `--no-control-socket` (`control_socket_disable`, checked in the
  locked package). Disabling the socket changes no behaviour MedHub uses.
- **A-5:** The pins record the versions in use when they are made: the action tags in use, the
  runtimes of the base images, and the uv version the lock was last checked with. They do not
  upgrade anything.

## Open questions

For the human, each with a recommended answer.

- **Q-1 (PRB-038 already fixed):** CR-004 TASK-203 fixed PRB-038 without a `resolves` link, and
  CR-004 is `closed`. *Recommended:* CR-005 resolves PRB-038 by verification only (AC-9), with a
  `## Resolution` that cites TASK-203 and commit `4b1daf5`. CR-004 is not reopened.
- **Q-2 (enforcement):** PRB-034 and PRB-040 only say to "consider" a check. *Recommended:* yes,
  extend the CI checks to tooling references and to the test container image (AC-4, AC-6). Without
  a check, a later edit can bring a floating reference back unnoticed, which is how PRB-040 grew
  from two call sites to nine.
- **Q-3 (`init: true`):** *Recommended:* out of scope. No defect has been observed, and the
  Gunicorn bug it guards against is fixed in 26.1.0, which a SOUP upgrade will bring.
- **Q-4 (SR-028 amendment):** Approve SR-028 1.7 (AC-8, AC-9) as written, or prefer a separate SR
  for build and verification tooling? *Recommended:* approve the amendment (precedent CR-001,
  CR-002).

**Decisions (2026-11-12, Carlos Santiago Liceras, Specify gate):** Q-1 to Q-4 answered as
recommended. PRB-038 is resolved by verification only; CI checks are extended (AC-4, AC-6);
`init: true` is out of scope; SR-028 1.7 is approved as written.

**Decisions (2026-11-12, Carlos Santiago Liceras, plan gate):** the §7.4 change analysis, RISK-010
1.6 (residual 3×1 acceptable), the risk introduced by the controls and the decision not to reopen
RISK-001, 006, 007 and 011 are accepted. Q-5 to Q-7 answered as recommended: TASK-216 adds the
tool-pin review to PLAN-002 (1.3); `runs-on: ubuntu-latest` stays and is recorded as a documented
limit in ADD-024 and RISK-010; TASK-214 `implements` SR-041. The version choices (uv 0.13.7, the
action SHAs from run 42779806388, the redocly release before that run) and TASK-209..216 are
approved; ADR-0020 is Accepted.

**Plan-stage questions (open, 2026-11-12, Software Architect role).** For the human at the plan
gate, each with a recommended answer.

- **Q-5 (review cadence for the tool pins):** the Risk impact above names "the PLAN-002 cadence" as
  the counterweight to pinned tools, but PLAN-002 "SOUP monitoring" covers `soup` records only,
  and the tools are not SOUP. *Recommended:* yes, TASK-216 adds one paragraph to PLAN-002 (1.3,
  `in_review`): the SR-028 AC-8 tool pins are reviewed with the SOUP list, before every release
  and at most 365 days apart, and moved only by a reviewed commit. No automated update tooling
  (out of scope).
- **Q-6 (hosted runner image):** every job runs on `runs-on: ubuntu-latest`, which GitHub moves
  (it was `ubuntu-26.04`, image 20261101.186.1, on 2026-11-10); the image also supplies Docker,
  Compose, the system `pip` and `openssl`. A label such as `ubuntu-26.04` fixes the OS release but
  not the image, which GitHub still updates weekly; no repository reference can pin it.
  *Recommended:* leave `runs-on` unchanged and record the runner image as a documented limit of
  SR-028 AC-8 in ADD-024 and RISK-010 (path 3): no released image is built on it, and every tool
  the repository installs on it is pinned. Alternative: pin the label to `ubuntu-26.04` and add it
  to the check (one more rule, TASK-209/211).
- **Q-7 (trace of the PRB-041 task):** TASK-214 has no SR to implement (Requirements decision).
  *Recommended:* it links `implements` SR-041, the requirement of the deployment item it changes
  (ADD-026), as CR-004 TASK-208 did, and its body says no SR-041 criterion changes.

## Change analysis (Risk stage, §7.4, 2026-11-12)

The Software Architect role ran this analysis. Scales and matrix: `docs/medtrace.yml` (5 × 5
`risk_matrix`) and PLAN-005.

- **Records consulted:** RISK-001, 006, 007, 010, 011; SR-028 1.7, SR-041; ADD-024, ADD-026;
  SOUP-001, 005, 020, 021; TS-013; PLAN-001, 002, 003, 005; ADR-0019; the four PRBs; CR-001 and
  CR-004 (precedent).
- **Code read:** `.github/workflows/ci.yml`, `backend/Dockerfile`, `frontend/Dockerfile`,
  `infra/docker-compose.yml`, `infra/check_image_pins.py` and its tests, `infra/smoke-test.sh`,
  `backend/tests/db/conftest.py` and every `PostgresContainer` call site,
  `backend/modules/dicom_viewer/tests/conftest.py`.
- **Hosted evidence read:** the job logs of run 42779806388 (2026-11-10, head `d53eb7f`, all jobs
  green). Every Python job ran **CPython 3.12.16** while the image ships 3.12.15 (SOUP-001); every
  Python job installed **uv 0.13.7**; the actions resolved to checkout `11d5960a…7262`,
  setup-python `a26af69b…7065`, setup-node `49933ea5…0020`; the runner was `ubuntu-26.04`.
  PRB-034's "can use different tools" is therefore observed, not only possible.

**Findings beyond the Specify-stage scope** (all inside SR-028 AC-8 and AC-9 as approved; none
changes an AC's intent):

- **F-1:** the OpenAPI Lint job runs `npx --yes @redocly/cli` with no version: a CI tool that
  floats, which PRB-034 did not list. Pinned in TASK-209 and covered by the TASK-211 rule (the
  Boundaries forbid leaving a real reference outside the check).
- **F-2:** the floating `postgres:16` has **eleven** call sites, not nine: two more in
  `backend/modules/dicom_viewer/tests/` (`test_audit_module_key.py:78`,
  `test_failure_audit_persistence.py:36`). AC-5's "nine at HEAD" reads eleven; TASK-212 moves all.
- **F-3:** the `backend-tests` CI service containers (`postgres`, `redis`) are test containers of
  SOUP components, so SR-028 AC-9 covers them. They equal Compose today; TASK-213's rule keeps them
  equal.

**A-3 holds.** `actions/python-versions` `versions-manifest.json` (fetched 2026-11-12) lists 3.12.15
as stable for linux x64 and arm64 on Ubuntu 22.04, 24.04 and 26.04, so `actions/setup-python` with
`python-version: "3.12.15"` installs it on the current runner. Node.js 24.22.2 is in
`actions/node-versions` and on nodejs.org. No fallback such as `uv python install` is needed.

**Conclusion.** `risk_impact: affects_controls` is **confirmed**.

- **§7.4.1: no new hazard; class B unchanged.** The change touches CI configuration and the pin
  check (SI-DEVINFRA, not deployed), backend test code (not shipped), the `uv` install of the image
  build stage and one Gunicorn flag (SI-DEPLOY). No runtime code, schema, API or data path
  changes. The only shipped effects are the same installed set (AC-10) and one management
  interface fewer. No harm beyond those already in RISK-001, 006, 007, 010 and 011 is reachable.
- **§7.4.2: controls affected.** RISK-010 is the only record whose control set changes; it gains
  path 3 and three control rows (revised to 1.6, `in_review`). For RISK-006 and RISK-011 the
  controls are unchanged and their verification is strengthened: the real-database evidence (TS-009
  TC-009.9, .11; TS-008 TC-008.10) then runs on SOUP-020's exact image. For RISK-007 the log signal
  its monitoring control relies on is restored. For RISK-001 the SR-041 AC 2 guard gets a
  fresh-volume record (PRB-038). These four records are **not** reopened: their scores, controls and
  residual arguments do not depend on the change, and TASK-216 reopens one only if the evidence
  contradicts this analysis.
- **New causes introduced by the change itself**, each with a control in the plan:
  1. a wrong `uv` pin changes what the image installs (RISK-010, RISK-007): one version, the one
     hosted CI last verified with; `uv lock --check` with it; the installed set compared before and
     after (AC-10, TASK-210);
  2. a wrong Gunicorn flag stops the backend or changes its behaviour (RISK-007): the flag is
     checked in the locked package (A-4); infra test on the `CMD`; started stack answers a login
     and logs no ERROR (AC-8, TASK-214);
  3. CI moves from Python 3.12.16 to the shipped 3.12.15: a test could behave differently on the
     shipped patch. That is the intent, and the full suites on hosted runners show it (AC-12);
  4. a SHA that names no release, or the wrong one, would pin an unreviewed action: each SHA is
     the one the last green run resolved, matched to its release tag (AC-1, TASK-209);
  5. pinned tools no longer receive upstream fixes on their own (RISK-010 "Risks introduced by
     controls"): CI only, no product path; counterweight a review cadence (Q-5);
  6. the extended check can reject a correct change (false positive): it only blocks a merge; forms
     it cannot parse fail, never pass (ADR-0020).
- **Safety-relevant SRs and their RISK coverage.** SR-028 → RISK-007, RISK-010 (`mitigates`,
  unchanged); SR-041 → RISK-001, 005, 011 (unchanged). No new SR, no new risk-control SR (§5.2.3):
  AC-8 and AC-9 of SR-028 are the risk-control requirements and were approved at the Specify gate.

| Change (tasks) | Software items | §7.4.1 contribution | §7.4.2 controls affected | §7.4.3 verification |
|---|---|---|---|---|
| Actions by SHA, CI Python and Node at base-image patch, linter pinned (209) | SI-DEVINFRA | None; CI evidence now on the shipped Python. New: cause 3, 4 | RISK-010 (new control); RISK-006, 011 evidence | TS-013 TC-013.12; hosted logs (216) |
| One exact `uv` in image and CI (210) | SI-DEVINFRA, SI-DEPLOY (build stage) | None if the installed set is equal. New: cause 1 | RISK-010 (new control) | AC-10 comparison; TC-013.12 |
| Pin check: tool rules (211) | SI-DEVINFRA | None. New: cause 6 | RISK-010 (new protective control) | TS-013 TC-013.11; negative control |
| Test PostgreSQL from one pinned definition (212) | backend tests | None | RISK-006, RISK-011 (verification strengthened), RISK-010 | TS-013 TC-013.14; digest assertion |
| Pin check: test images equal deployment (213) | SI-DEVINFRA | None. New: cause 6 | RISK-010 (new protective control) | TS-013 TC-013.13; negative control |
| Gunicorn `--no-control-socket` (214) | SI-DEPLOY (backend image) | Removes a default-on unused interface and a false ERROR. New: cause 2 | RISK-007 (log signal restored) | Infra test; started stack (AC-8) |
| Fresh-volume bring-up (215) | SI-DEPLOY | None (verification only) | RISK-001 (SR-041 AC 2 evidence) | AC-9 record |

**Residual scores.** None changes. RISK-010 3 × 1 → acceptable (path 3 at probability 1);
RISK-006 2 × 2 → acceptable; RISK-007 3 × 2 → alarp; RISK-011 3 × 2 → alarp; RISK-001 2 × 2 →
acceptable. Acceptability is the `risk_matrix` cell, not a judgement.

**For the human to accept** (risk acceptability is the human's decision):

1. This conclusion: `affects_controls`, no new hazard, class B unchanged, no new risk-control SR.
2. RISK-010 1.6 (`in_review`): path 3, the three new control rows and the unchanged residual
   3 × 1 → acceptable. Its approval is the acceptance.
3. That RISK-006, RISK-007, RISK-011 and RISK-001 are not reopened (their residuals stand).
4. The risk introduced by the controls: pinned CI tools do not pick up upstream fixes on their own,
   with the review cadence of Q-5 as the counterweight.
5. The residual limit of Q-6: the hosted runner image is not pinned by any repository reference.

## Plan

The plan is the TASK records below (overlay: no `docs/plans/<feature>.md`). Nothing starts until
the human approves the plan, ADR-0020 (`Proposed`) and RISK-010 1.6.

- All tasks on `bug/build-hygiene`, one commit per QA-approved task with its records.
- An `approved` record that several tasks change is bumped and has its approval cleared once, by
  the first task that changes it; later tasks add to the same version (CR-002 rule): TS-013 1.6
  (TASK-211, 212, 213), ADD-024 1.3 (TASK-211, 213). Changed by one task: ADD-026 1.5 and SOUP-005
  1.3 (TASK-214), PLAN-002 1.3 (TASK-216, only if Q-5 = yes).
- **"Ask first"** (Boundaries): TASK-209 if a SHA matches no exact release tag; TASK-210 if
  `uv lock --check` fails with 0.13.7; TASK-212 if testcontainers cannot start an image by digest.
  Pushing for the hosted run (TASK-216) needs the human's go-ahead.

| Order | Task | PRB | CR AC | SR (AC) | RISK (`mitigates`) | Size | Depends on |
|---|---|---|---|---|---|---|---|
| 1 | [TASK-209](../design-outputs/tasks/TASK-209-pin-github-actions-ci-runtimes-and-openapi-linter.md) Pin actions, CI runtimes, OpenAPI linter | 034 | AC-1, AC-2 (F-1) | SR-028 AC-8 | 010 | S | — |
| 2 | [TASK-210](../design-outputs/tasks/TASK-210-pin-uv-in-backend-image-and-ci.md) One exact uv in image and CI | 034 | AC-3, AC-10 | SR-028 AC-8 | 010 | S | 209 |
| 3 | [TASK-211](../design-outputs/tasks/TASK-211-extend-pin-check-to-build-and-ci-tooling.md) Pin check: tool references | 034 | AC-4, neg. control | SR-028 AC-8 | 010 | M | 209, 210 |
| P1 | [TASK-212](../design-outputs/tasks/TASK-212-one-pinned-postgresql-image-for-database-tests.md) Test PostgreSQL from one pinned definition | 040 | AC-5, AC-7 | SR-028 AC-9 | 010 | M | — (parallel with 1–3) |
| — | **Checkpoint A** | | | | | | 1–3, P1 |
| 4 | [TASK-213](../design-outputs/tasks/TASK-213-check-test-images-equal-the-deployment.md) Pin check: test images equal deployment | 040 | AC-6, neg. control | SR-028 AC-9 | 010 | M | 211, 212 |
| 5 | [TASK-214](../design-outputs/tasks/TASK-214-disable-unused-gunicorn-control-socket.md) Gunicorn control socket off | 041 | AC-8, neg. control | SR-041 (Q-7) | 007 | S | 210 |
| 6 | [TASK-215](../design-outputs/tasks/TASK-215-fresh-volume-bring-up-from-the-template.md) Fresh-volume bring-up | 038 | AC-9 | SR-041 AC 2, AC 4 | 001 | XS | 214 |
| — | **Checkpoint B** (started stack) | | | | | | 4–6 |
| 7 | [TASK-216](../design-outputs/tasks/TASK-216-verify-cr-005-end-to-end.md) Verify end to end (**Checkpoint C**) | all | AC-11, AC-12, AC-13 | SR-028 | 010 | S | all above |

**Shared files (sequential).** `.github/workflows/ci.yml` (209 → 210); `backend/Dockerfile`
(210 → 214); `infra/check_image_pins.py` and `infra/tests/test_check_image_pins.py` (211 → 213).
TASK-212 shares no file with 209..211 and can be committed between any two of them.

**Checkpoints.**

- **A** (after 1–3 and P1): `python3 -m unittest discover -s infra/tests` and
  `python3 infra/check_image_pins.py` green; backend suite (coverage ≥ 85 %) and DICOM module
  suite green with the real-database tests on the SOUP-020 digest; the backend image's installed
  set unchanged.
- **B** (after 4–6, started stack): the extended check green on the repository and red on every
  negative control; a fresh-volume stack from the template starts, `infra/smoke-test.sh` reports
  0 failed, the backend log has no ERROR line.
- **C** = TASK-216 (hosted run, records, `traceability-check`).

**CR AC coverage.** AC-1 → 209; AC-2 → 209; AC-3 → 210; AC-4 → 211; AC-5 → 212; AC-6 → 213;
AC-7 → 212; AC-8 → 214 (and 215 on a fresh volume); AC-9 → 215; AC-10 → 210; AC-11 → 211, 213,
214, 215 (records and PRB resolutions), 216; AC-12 → 216; AC-13 → 216; negative control → 211,
213, 214, re-run in 216.

**SR coverage.** SR-028 AC-8 → 209, 210, 211; SR-028 AC-9 → 212, 213; SR-041 AC 2, AC 4 → 215
(verification); SR-041 (trace only, Q-7) → 214.

**ADD coverage** (class B): SR-028 → ADD-024 (`U-INF-CIPipeline`, revised by 211 and 213);
SR-041 → ADD-026 (backend command, revised by 214).

**Test specifications.**

| TS | Change | Test cases | Tasks |
|---|---|---|---|
| TS-013 | 1.5 → 1.6 | TC-013.11 tool rules (unit); TC-013.12 tool pins in the repository and on hosted CI (integration, review of the SHA-to-tag record); TC-013.13 test-image rules (unit); TC-013.14 test containers on the SOUP-020 digest (integration) | 211, 209, 210, 213, 212 |

The Gunicorn command test (TASK-214) has no SR criterion and no TS case (Requirements decision);
ADD-026's Verification section names it.

**SOUP touched** (no version change, so no new anomaly review): SOUP-005 Gunicorn (control socket
disabled by configuration, 214); SOUP-020 PostgreSQL and SOUP-021 Redis (their references now also
bind the test containers; no record change needed); SOUP-001 Python (CI runs its exact version; no
record change). CI tools, `uv` and the linter are not SOUP (none ships).

**Architecture decision.** [ADR-0020](../design/adr/0020-tool-and-test-image-pins-in-the-pin-check.md)
(`Proposed`): extend `infra/check_image_pins.py` rather than add a mechanism; the shipped
references are the sources of truth. arc42: no section describes the pin check's scope, so no
arc42 change is planned; TASK-216 confirms.

### Plan risks

| Risk | Impact | Mitigation |
|---|---|---|
| A resolved SHA matches no exact release tag | Comment cannot name the release; AC-1 not met | Ask first (TASK-209); no silent upgrade |
| uv 0.13.7 reads the lock differently from the image's last build | Image content changes | AC-10 before/after comparison; `uv lock --check` with 0.13.7 |
| testcontainers cannot start `name:tag@digest` | Real-DB tests fail to start | Checked on the first run; ask first, never drop the digest |
| Tests behave differently on Python 3.12.15 than on 3.12.16 | Red CI | Intended exposure: fix as a PRB, not by moving the pin |
| Line-based check misses or mis-parses a form | False negative or false positive | Unparseable forms fail; fixtures per form; negative controls |
| The hosted runner image changes under the pins | CI difference outside the repository | Q-6: documented limit; the hosted run is evidence for the date it ran |
| No Docker daemon on the workstation | AC-7, AC-8, AC-9, AC-10 cannot run locally | Reference workstation; CI runs the real-DB suites |

## Version history

- 1.0 (2026-11-12) — Created at the Specify stage (GitHub sancharly/medhub#34). `resolves`
  PRB-034, PRB-038, PRB-040 and PRB-041. SR-028 amended to 1.7 (`in_review`). The four PRBs gained
  or updated their `## Investigation`.
- 1.1 (2026-11-12) — Specify gate passed: the human answered Q-1 to Q-4 as recommended and
  approved SR-028 1.7.
- 1.2 (2026-11-12) — Risk and Plan stages (Software Architect role). Status stays `open`.
  - "Change analysis (Risk stage)": `affects_controls` confirmed, no new hazard, class B
    unchanged; A-3 confirmed; findings F-1 (floating OpenAPI linter), F-2 (eleven test call sites,
    not nine), F-3 (CI service containers in AC-9 scope); hosted evidence that CI ran Python
    3.12.16. RISK-010 revised to 1.6 (`in_review`); RISK-001, 006, 007, 011 not reopened.
  - Plan: TASK-209..216 created (`draft`); checkpoints A–C; AC, SR, ADD, TS and SOUP coverage;
    plan risks. ADR-0020 (`Proposed`). New open questions Q-5 (tool-pin review cadence), Q-6
    (hosted runner image), Q-7 (trace of TASK-214). `relates_to` links to the tasks, RISK-001,
    RISK-011 and SOUP-021.
- 1.3 (2026-11-12) — Plan gate passed: the human accepted the change analysis and RISK-010 1.6,
  answered Q-5 to Q-7 as recommended and approved the plan; ADR-0020 Accepted.
- 1.4 (2026-11-13) — Wording correction, not a scope change (TASK-215 QA LOW 1, carried to TASK-216):
  AC-9 said "80 checks at HEAD"; the smoke test reports 78 for the stack as shipped, and two more for
  each extra running container (TASK-202's 80 included a scratch `smtp-catcher`). No criterion
  changes.
