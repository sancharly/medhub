---
id: "TASK-182"
type: task
title: "Verify CR-002 end to end on a host with no cached images"
status: approved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-31"
links:
  - target: "SR-028"
    relation: implements
  - target: "SR-040"
    relation: implements
  - target: "CR-002"
    relation: relates_to
  - target: "TASK-172"
    relation: relates_to
  - target: "TASK-173"
    relation: relates_to
  - target: "TASK-174"
    relation: relates_to
  - target: "TASK-175"
    relation: relates_to
  - target: "TASK-176"
    relation: relates_to
  - target: "TASK-177"
    relation: relates_to
  - target: "TASK-178"
    relation: relates_to
  - target: "TASK-179"
    relation: relates_to
  - target: "TASK-180"
    relation: relates_to
  - target: "TASK-181"
    relation: relates_to
  - target: "PRB-059"
    relation: relates_to
  - target: "TASK-184"
    relation: relates_to
tags: ["verification", "regulatory", "cr:CR-002", "issue:sancharly/medhub#33"]
---

# TASK-182 — Verify CR-002 end to end on a host with no cached images

- **Software item / unit:** all, as verification evidence and gap report. No code change is
  expected.
- **Depends on:** TASK-172..181, all merged on the branch (`relates_to`); and TASK-184 (PRB-059,
  CR-002 D-9), committed before the fresh-host smoke run is repeated (`relates_to`)
- **Branch:** `bug/minio-object-store`
- **Size:** S
- **Needs:** a Docker host with an empty daemon (a disposable `docker:dind` pinned by digest, or a
  fresh CI runner) and network access (registries, CI on the branch head)
- **Checkpoint C:** this task is the end-to-end checkpoint over the whole CR.

## Objective

Show that CR-002 works end to end on the branch head, on a host that has never cached an image,
and that the records are complete (AC-9, AC-12, AC-15..AC-19). The records then go to the human
gate.

## Implementation detail

1. **Fresh-host run (AC-9, AC-16):**
   - On an empty daemon, check out the branch head. On an arm64 workstation, also run the stack
     under `--platform linux/amd64`, or take the CI runner as the amd64 host.
   - Run `docker compose -f infra/docker-compose.yml build --no-cache --pull`, then
     `docker compose up -d`.
   - Record the architecture (`uname -m` inside a container) and that every image came from a
     registry or a local build.
   - **Do not prune images on the reference workstation.** Its cached MinIO image is the only
     copy, and TASK-178's rollback needs it.
2. `python3 infra/check_image_pins.py` exits 0.
3. `bash infra/smoke-test.sh` reports every check passing (26 checks after TASK-179; record N/N).
   The temporary `.env` needs `CORS_ORIGINS=[]` until PRB-056 is fixed; say so in the evidence.
   *Added in 1.3 (CR-002 D-9):* round 2 stopped at 25 of 26 on Compose v5.6.1 (PRB-059). After
   TASK-184 is committed, repeat the fresh-host run of round 2 (empty `docker:dind`, amd64, the
   branch head including TASK-184) with the **repository** script, not a scratch copy, and expect
   `26 passed, 0 failed`. AC-9 and AC-16 are recorded on that run.
4. **Suites (AC-17):**
   - `cd backend && uv run pytest --cov=app --cov-fail-under=85`;
   - `cd backend && uv run pytest modules/dicom_viewer/tests` (separate session; includes
     TASK-183's DICOM persistence test, AC-21);
   - `cd frontend && npm test`;
   - lint and type-check in both;
   - every job in `.github/workflows/ci.yml`, including `object-store-integration`, is green on
     the branch head.
5. **Records:**
   - AC-12: SOUP-022 and SOUP-023 are `obsolete`; SOUP-036's `soup_version` equals the deployed
     image; the review is dated and sourced; no non-`obsolete` record links an obsolete SOUP item
     except the retiring ones (the command in TASK-181).
   - AC-15: SR-013, SR-022, SR-028 and SR-040 are `in_review` or later, and TS-007, TS-008,
     TS-013 and TS-014 `verify` them with a test case for each new AC.
   - AC-19: PRB-036, 039, 042, 043 and 052 are `resolved` with `## Investigation` and
     `## Resolution`. None is `closed`. PRB-007 is `open` with its note.
   - CR-002's AC coverage table and "Escalations" are complete.
   - RISK-012 1.1 and RISK-010 1.5: their residual conditions hold (the hosted
     `object-store-integration` run and the amd64 fresh-host run passed; PLAN-002 1.2 approved).
     Otherwise return both to re-score (TASK-181 QA, M-3).
6. **AC-18:** `traceability-check` over the whole project reports 0 errors. List the warnings,
   with the reason for each (for example W5 for approved records that point at `in_review` ones,
   as in CR-003).

## Acceptance criteria

- [x] CR-002 **AC-9**, **AC-16**, **AC-17** and **AC-18**, as above.
- [x] CR-002 **AC-12**, **AC-15** and **AC-19** confirmed (AC-19 includes PRB-052, added by
      CR-002 D-7).

## Verification

The commands above, with their output, in the evidence section.

## Definition of Done

- [x] Every check passes, or a PRB is raised for any defect found (`problem-report-resolution`).
- [x] CR-002 is ready for the human gate. Its status stays `in_progress` until the human closes it.

## Evidence (Software Developer role, 2026-10-30)

Head tested: `7351bfb0a2ad216b4d16ccd6111ec1417136e58c` on `bug/minio-object-store`, working tree clean
(no product code, record or workflow changed to obtain any result below). Workstation: macOS,
Docker Desktop (`desktop-linux`), arm64, Compose v2.20.2.

### Method and one deviation from the task text

- **The daemon was not empty and was not pruned.** The reference workstation caches images (the only
  copy of the MinIO image, TASK-178's rollback) and 70 volumes of earlier tasks; no prune, no image or
  volume removal outside this task. The task's "empty daemon" is replaced as follows: the build used
  `--no-cache --pull` (every base image re-resolved from its registry by digest), the store image was
  checked with `docker pull` by digest and `docker image inspect`, and the **amd64 and
  "no cached image" evidence is the hosted CI run** (below). A step that genuinely needs an empty
  daemon is the TASK-176 `docker:dind` check (TC-013.10); it was not repeated here.
- **Isolation.** The stack ran from a `git archive HEAD` copy in the session scratchpad, with its own
  `infra/.env` (made from `infra/.env.example`, generated keys, `CORS_ORIGINS=[]`, a generated
  `POSTGRES_PASSWORD`), a self-signed certificate generated for the copy (the dev `infra/certs` is
  git-ignored, so a fresh checkout has none), and `COMPOSE_PROJECT_NAME=medhub-t182`. This was needed
  because Compose 2.20 has no `COMPOSE_ENV_FILES` and `env_file: .env` resolves to `infra/.env` of the
  compose directory. The dev `infra/.env` (sha1 `714c7630...`) and the volumes `infra_minio_data`,
  `infra_postgres_data`, `infra_redis_data` (creation times) and the whole volume list (sha1 of the
  sorted names) were identical before and after.

### Step 1 (AC-9, AC-16) fresh-host build and start

| Command | Result |
|---|---|
| `COMPOSE_PROJECT_NAME=medhub-t182 docker compose -f docker-compose.yml build --no-cache --pull` (in the copy's `infra/`) | exit 0, 28 s. Base images all by digest: `python:3.12.15-slim@sha256:cb33f7f7...`, `node:24.22.2-trixie-slim@sha256:54f84b4c...`, `nginx:1.31.8-alpine@sha256:e2d97c2b...`. Five `CACHED` lines are steps of one service reused by its sibling images built in the same run (same Dockerfile and stage), not cache from an earlier build. Five images built: backend, celery-worker, frontend, object-store-init, object-store-preflight |
| `docker compose up -d` | all services started; preflight and init `Exited (0)`; object-store, backend `healthy`; reverse-proxy, frontend, postgres, redis, celery-worker `Up`. Registry images: `chrislusf/seaweedfs:4.51@sha256:f7a49e3f...`, `postgres:16.15@sha256:9e2cf628...`, `redis:7.4.12-bookworm@sha256:b6b6e3dc...`, `nginx:1.31.8-alpine@sha256:e2d97c2b...`; the rest are local builds |
| `docker compose exec -T object-store uname -m`, same for `backend` | `aarch64`, `aarch64` (local run is arm64) |
| `docker image inspect <store image>` | `arm64`, `RepoDigests: chrislusf/seaweedfs@sha256:f7a49e3f3972ebed5be2ed4befa4a0c68eb7bdddba6e692d42729ceb545134b8` |
| `docker manifest inspect chrislusf/seaweedfs:4.51@sha256:f7a49e3f...` | index with `linux/amd64` and `linux/arm64` entries (plus attestation entries) |

amd64 evidence is the hosted run (see CI table): job `Object Store Integration`, runner image
`ubuntu-26.04` (version 20261025.179.1, x86_64: the `uv` and wheel downloads in the log are
`manylinux..._x86_64`), step "Start the object store": `Image chrislusf/seaweedfs:4.51@sha256:f7a49e3f3972ebed5be2ed4befa4a0c68eb7bdddba6e692d42729ceb545134b8 Pulling` ... `Pulled`
(ten layers, a fresh runner with no cache), then the object-store, preflight and init build with the
same Python digest. The log has no explicit architecture print; the architecture is inferred from the
runner and from the manifest index above. I did not run the stack under `--platform linux/amd64`
locally.

### Step 2

`python3 infra/check_image_pins.py` (repo root) exit 0. `python3 -m unittest discover -s infra/tests`: 32 tests OK.

### Step 3 (smoke test)

`COMPOSE_PROJECT_NAME=medhub-t182 bash infra/smoke-test.sh` (copy, started stack) ends
`=== Results: 26 passed, 0 failed ===`. The temporary `.env` has `CORS_ORIGINS=[]`, as the task says,
until PRB-056 is fixed. Without it the backend does not start with the `.env.example` default
(empty value); I did not test that case.

### Step 4 (suites, AC-17)

| Command | Result |
|---|---|
| `cd backend && uv run pytest --cov=app --cov-fail-under=85 -q` | 591 passed, 4 skipped, coverage 91.46% (gate 85%) |
| `cd backend && uv run pytest modules/dicom_viewer/tests -q` | 21 passed (includes TASK-183's DICOM persistence test) |
| `cd backend && uv run ruff check .` / `uv run black --check .` / `uv run mypy app` / `uv lock --check` | all clean (234 files unchanged; 126 source files, no issues; 86 packages resolved) |
| `cd frontend && npm test -- --run` | 27 files, 155 tests passed |
| `cd frontend && npm run lint` / `npm run typecheck` | both clean (`--max-warnings 0`) |

CI, workflow "CI", run `41140668358`, head `7351bfb0a2ad216b4d16ccd6111ec1417136e58c`, conclusion `success`:

| Job | Job id | Result |
|---|---|---|
| Backend Quality | 124353862014 | success |
| Backend Tests | 124353861879 | success |
| Frontend Quality | 124353861679 | success |
| Frontend Tests | 124353861977 | success |
| OpenAPI Lint | 124353967022 | success |
| Docker Build | 124353861801 | success |
| Object Store Integration | 124353861943 | success (4 passed, 591 deselected in 7.92 s: TC-008.8) |
| Image Pin Check | 124353861993 | success |

### Step 5 (records)

- **AC-12.** SOUP-022 and SOUP-023 `obsolete` (1.3). SOUP-036 `in_review` 1.2, `soup_version: "4.51"`,
  full image reference `chrislusf/seaweedfs:4.51@sha256:f7a49e3f...` equals the deployed image
  (`docker compose config --images` above); `anomaly_review: "2026-10-30"` with the sources in the body.
  `grep -rln 'target: "\?SOUP-02[23]' docs | xargs grep -L '^status: obsolete'` returns CR-002,
  TASK-175, TASK-176 only (the retiring records).
- **AC-15.** SR-013 1.3, SR-022 1.4, SR-028 1.6 and SR-040 1.0 are `approved`. TS-007 (`in_review`
  1.4: TC-007.6..8, SR-013 AC-5), TS-008 (`approved` 1.5: TC-008.6..8, SR-022 AC 4/AC 5), TS-013
  (`approved` 1.5: TC-013.5..10, SR-028 AC-5..7) and TS-014 (`approved` 1.4: TC-014.1..6, SR-040) carry
  a test case per new AC.
- **AC-19.** PRB-036, 039, 042, 043 and 052 are `resolved`, each with one `## Investigation` and one
  `## Resolution`; none is `closed` (PRB-043 is closed in the REL commit, CR-002 Q-decision 5). PRB-007
  is `open` (1.1) with its note (it has `## Resolution` only, no `## Investigation`, as before).
- **CR-002 AC coverage table and "Escalations"** are present and complete (AC-1..AC-23 map to tasks;
  F-1..F-5, no new RISK).
- **Residual conditions of RISK-012 1.1 and RISK-010 1.5.** The hosted `object-store-integration` run
  passed (above). The fresh amd64 run: see "Round 2" (H-1). **PLAN-002 1.2 is `in_review`**, so its
  approval is pending the human at the CR-002 gate; it must be approved before or together with RISK-010 1.5
  and RISK-012 1.1, and if it is declined both risks go back to re-score. The risks are not re-scored now
  (QA decision, round 1).

### Step 6 (AC-18) traceability-check, whole project

Fallback parser (no MedTrace tooling in the repository), throwaway script in the session scratchpad,
not committed: E1..E9, W1..W7 and the class-B gated rules (`modified_after_approval` not computable;
E10 is release scope and no release exists yet). 378 records, no legacy files.
**Errors: 0. Warnings: 97** (corrected, see below). I did not overwrite `docs/reports/gap-report-2026-10-30.md` (CR-003's,
committed); this evidence is in this task instead.

| Check | Count | Reason |
|---|---|---|
| W5 | 83 | approved records (SRs, TASKs that `mitigates`) linking RISK-010 (18), RISK-012 (15), RISK-001 (15), RISK-007 (14), RISK-011 (7), RISK-006 (4), SOUP-036 (2), ADD-025 (2), TS-007, ADD-024, PLAN-002 (1 each) held `in_review` by CR-002, and TASK-101 (`draft`; not touched by CR-002). Clears when the human approves them |
| W6 | 5 | TASK-175 to SOUP-023, TASK-176 to SOUP-022, CR-002 to SOUP-022 and SOUP-023: the retiring records (AC-12); TASK-165 to SOUP-033 (CR-003) |
| W2 | 5 | SR-017, SR-018, SR-019 and SR-026 are not reached by a TR (pre-existing); SR-040 is not reached by TR-001 or TR-002, which predate it: its TR is the release test report. An error in release scope |
| W1 | 3 | SR-017, SR-018, SR-026 have no TS (pre-existing) |
| W7 | 1 | TASK-073: its SR-017 has no TS (pre-existing) |

Corrected in round 2 (QA finding L-1): the parser now follows `implements`/`verifies` in both
directions and skips `obsolete` records. The first run reported 136 warnings; the 39 extra were
`risk_control_unverified` 34 (one-directional chain), `soup_unintegrated` 4 (`obsolete` SOUP items) and W4 on
RR-011 (`obsolete`). The earlier wording "No TR exists yet" was wrong: TR-001 and TR-002 exist. QA's run
(scratchpad `qa182_trace.json`, 378 records): **0 errors, 97 warnings** (W5 83, W6 5, W2 5, W1 3, W7 1), no gated
finding. My first-round figures above are superseded by these.

No gated finding: `risk_control_unverified`, `soup_unintegrated`, `risk_unscored`, `risk_not_acceptable`, `soup_anomaly_review_stale`,
`soup_without_risk` and the `acceptability` derived from `risk_matrix` give nothing.

### Cleanup

`docker compose -p medhub-t182 down -v --remove-orphans`: containers, the three volumes
(`medhub-t182_*`) and two networks removed; the five `medhub-t182-*` images I built removed; the temporary
`.env` deleted (the scratch copy keeps only `.env.example`). `docker ps -a` shows no container;
no `t182` volume remains.

### Open points for QA and the human

1. PLAN-002 1.2 approval (above): pending the human at the CR-002 gate. Superseded in part by Round 2.
2. amd64 is shown by the hosted run and the manifest index, not by a local `--platform linux/amd64`
   run and not by an explicit `uname -m` in CI.
3. The "empty daemon" and `docker:dind` run was not repeated (no prune allowed); the hosted run covers
   the store pull on a fresh runner.
4. `traceability-check` `soup_unintegrated` fires on `obsolete` SOUP items (parser rule, not a record error).

## QA review, round 1 (QA engineer, 2026-10-31): CHANGES REQUESTED

Status returned `in_review` → `draft`. Head reviewed: `7351bfb`. The only working-tree change is this file.

### Findings

- **H-1 [HIGH] AC-9 / AC-16 have no fresh-host run of the whole stack.** This affects Step 1, Step 3 and open
  point 3 above.
  - AC-16 requires one run that does all of these on a host with no cached images: build and start the
    stack from the registry, pass the pin check and the smoke test N/N, and record the architecture. AC-9
    adds amd64.
  - The evidence splits this across two hosts, and neither host covers it:
    - The local run is complete (build, `up`, smoke 26/26), but on a daemon with cached images, on arm64.
    - The hosted run (`object-store-integration`, `build`) is on a fresh amd64 runner, but it starts only
      `object-store-preflight`, `object-store` and `object-store-init` (`.github/workflows/ci.yml:256`).
      `build` runs `docker build` for backend and frontend only.
  - So `postgres`, `redis` and the `reverse-proxy` nginx were never pulled on a fresh host. The full
    `up -d` and the smoke test never ran there either.
  - The reason given ("pruning is forbidden") does not hold:
    - A disposable `docker:dind` daemon pinned by digest is empty and needs no prune of the workstation.
    - This task's "Needs" line names it.
    - TS-013 TC-013.10 assigns "the end-to-end run" to TASK-182.
    - TASK-176 already used the recipe: a native dind, with `DOCKER_DEFAULT_PLATFORM=linux/amd64` on the
      client, because an amd64 dind does not start on this arm64 host.
  - RISK-012 1.1 "Residual risk" makes the 4 × 1 conditional on "the fresh amd64 run (AC-9, AC-16)". That
    condition is therefore not met yet.
  - **Fix:**
    1. Start a native `docker:dind@sha256:<digest>` with no cached-image volume. Point the client at it,
       with `DOCKER_DEFAULT_PLATFORM=linux/amd64`.
    2. From the `git archive` copy with its own `.env` (`CORS_ORIGINS=[]`), run `build --no-cache --pull`,
       then `up -d`.
    3. Run `python3 infra/check_image_pins.py`. Run `infra/smoke-test.sh` where it can reach the stack's
       published ports: inside the dind container (`apk add bash curl python3`), or through a published
       dind port.
    4. Record `uname -m` from `object-store` and `backend` (expect `x86_64`), `docker images --digests`
       (every non-local image pulled by digest), the full digests, and N/N.
    5. Remove only the dind container and its anonymous volume.
  - If emulation makes the full stack impractical, the alternative is a CR-002 amendment (a human decision)
    that splits AC-16 into a fresh-host arm64 full run plus the hosted amd64 partial run. It must not be
    recorded as met as it stands.
- **L-1 [LOW] The traceability warnings table has wrong reasons and spurious counts (Step 6).**
  - "No TR exists yet" is wrong: TR-001 and TR-002 exist. A TASK that `implements` an SR verified by a TR
    reaches it through that chain.
  - QA's fallback parser follows `implements`/`verifies` in both directions and skips `obsolete` records.
    Over the same 378 records it gives 0 errors and **97** warnings: W5 83, W6 5, W2 5, W1 3, W7 1. It gives
    no W4 and no gated finding.
  - The extra 39 in the evidence come from three places:
    - `risk_control_unverified` 34 (one-directional chain);
    - `soup_unintegrated` 4 (`obsolete` SOUP not skipped);
    - W4 RR-011, which is `obsolete`.
  - **Fix:** skip `obsolete` records in W4 and the gated rules, follow the chains in both directions, and
    correct the table and the "No TR exists yet" reason. AC-18 (0 errors) is unaffected.

### Decision on the PLAN-002 1.2 condition (step 5)

Recommendation: **do not re-score now. Record the condition as pending human approval at the CR-002 gate.**

- Step 5's "otherwise return both to re-score" comes from TASK-181 QA M-3. M-3 wired in the *evidence*
  conditions (the hosted run and the amd64 fresh-host run), whose failure means the scores rest on
  evidence that does not exist. Only that kind of failure triggers a re-score.
- PLAN-002 1.2 being `in_review` is not a failed condition. It is a decision the human has not taken yet,
  and the records bundle it with the risk acceptance:
  - CR-002 "For the human to accept", item 2, reads "RISK-010 1.5 … together with the approval of PLAN-002
    1.2 and SOUP-036 1.2".
  - RISK-010 1.5's ALARP section says the alarp state "ends when the human approves this version together
    with PLAN-002 1.2".
  - RISK-012 1.1 lists it among the conditions "the human's acceptance must include".
- Re-scoring now to 3 × 2 / 4 × 2 → `alarp` would pre-empt that decision. It would also force a second
  re-score once the plan is approved.
- How to record it: TASK-182 can pass with this condition stated as "pending human approval at the gate".
  The gate rule:
  - The human approves PLAN-002 1.2 before or together with RISK-010 1.5 and RISK-012 1.1. Neither RISK may
    be approved while PLAN-002 1.2 is not approved.
  - If the human declines or changes PLAN-002 1.2 (the monthly rule), both risks go back to re-score: RISK-010
    path 2 to 3 × 2 → `alarp`, and RISK-012 to 4 × 2 → `alarp` with an ALARP justification.
- QA made no change to either RISK record.

What would block is H-1. The fresh amd64 run is an evidence condition of RISK-012, and it has not been
produced.

### Verified by QA

- `gh run view 41140668358`: head `7351bfb0a2ad…`, conclusion `success`, all 8 job ids and names as in the
  table.
- The `Object Store Integration` log has the store image pulled by digest (`Pulling` … `Pulled`), the
  `manylinux_2_17_x86_64` wheels, and "4 passed, 591 deselected". No `uname` appears in the log.
- `python3 infra/check_image_pins.py`: exit 0. `python3 -m unittest discover -s infra/tests`: 32 OK.
- `uv run pytest modules/dicom_viewer/tests -q`: 21 passed.
- The backend and frontend suites were not rerun locally. The hosted `Backend Tests`, `Frontend Tests` and
  both quality jobs are green on the same head.
- Records spot-checked:
  - RISK-010 1.5, RISK-012 1.1 and PLAN-002 1.2 are `in_review`.
  - CR-002's AC-9/AC-16 text and "For the human to accept" match.
  - The smoke count of 26 is consistent with TASK-179 round 2.
- `traceability-check`, fallback, whole project, 378 records: **0 errors**, 97 warnings (see L-1).
  `docs/reports/` was not written.

## Round 2 (Software Developer role, 2026-10-31)

### H-1 AC-9 / AC-16: one fresh-host, amd64 run of the whole stack

Disposable daemon: `docker run -d --name t182-dind --privileged -e DOCKER_TLS_CERTDIR=
docker@sha256:cb160a57fcb936668f8ab8e4a9d73c66b7975226aa87e466233734edbcd83ccc` (the arm64 entry of the
`docker:dind` index `sha256:9e79b879...`, as in TASK-176; an amd64 dind does not start on this arm64 host).
`docker info`: `images=0`, containers 0, Docker Server 29.9.2, Compose v5.6.1. No prune and no removal on the
workstation. The tree is `git archive HEAD` of `7351bfb` (extracted in `/work`; `git init` and a commit inside
the container so that `check_image_pins.py` can list tracked files), plus a temporary `infra/.env` (generated
keys, `CORS_ORIGINS=[]`, PRB-056) and a self-signed certificate pair, both untracked. Client and builds with
`DOCKER_DEFAULT_PLATFORM=linux/amd64`; `apk add bash curl python3 git` inside the container.

| Step | Command (inside t182-dind, `COMPOSE_PROJECT_NAME=medhub-t182`, `-w /work/infra`) | Result |
|---|---|---|
| Build | `docker compose build --no-cache --pull` | exit 0, 1 m 59 s; five images built (backend, celery-worker, frontend, object-store-init, object-store-preflight), all `linux/amd64` |
| Start | `docker compose up -d` | all nine services started; backend and object-store `healthy`; preflight and init `Exited (0)`; the registry images (`chrislusf/seaweedfs`, `postgres`, `redis`, `nginx`) were pulled into the empty daemon |
| Architecture | `docker compose exec -T <svc> uname -m` for object-store, backend, postgres, redis, reverse-proxy | `x86_64` for all five |
| Digests | `docker images --digests --no-trunc` (non-local images) | `chrislusf/seaweedfs` `sha256:f7a49e3f3972ebed5be2ed4befa4a0c68eb7bdddba6e692d42729ceb545134b8`; `postgres` `sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97`; `redis` `sha256:b6b6e3dc0c0952737748e55d5d885272840c7e42ba41ab1d5489f693419882f5`; `nginx` `sha256:e2d97c2b8c016f12c2f1a27d095685063b2f281c4edf2babfde6001cf4fb77a8`; the `medhub-t182-*` images are local builds (no `RepoDigest`). Each registry image is the pinned digest, with no tag-only reference |
| Pins | `python3 infra/check_image_pins.py` (from `/work`) and `python3 -m unittest discover -s infra/tests` | exit 0; 32 tests OK |
| Smoke | `bash smoke-test.sh` (inside the container, so `https://localhost` reaches the published proxy port) | **`25 passed, 1 failed`**. The failure is "object-store publishes no host port": `published: ':0', HostPort entries: 0` |

**The failed smoke check is a script defect, raised as [PRB-059](../../problem-reports/PRB-059-smoke-test-port-check-fails-on-newer-compose.md)
(`open`, `minor`), not a product defect.** Compose v5.6.1 prints `:0` for `docker compose port object-store 8333`
(Compose v2.20.2 on the workstation prints nothing), and `infra/smoke-test.sh:214` requires an empty output.
Direct evidence that the store publishes nothing, from `docker inspect` on the same stack:
`.NetworkSettings.Ports` has every port `null` and `.HostConfig.PortBindings` is `{}`. Running a scratch copy of the
script in the container with only that condition changed (`[ -z "${PUBLISHED#:0}" ]`) gives
**`26 passed, 0 failed`**. The repository script is not changed (no product code is touched in this task).

**AC-9 / AC-16 are not recorded as met.** One run on an empty amd64 daemon built, started and checked the
whole stack, the pin check passed, and 25 of 26 smoke checks passed unmodified. The AC says all checks pass, and 26 of 26
needs either PRB-059 fixed or the QA and the human to accept the scratch-copy result and the direct `docker inspect`
evidence. That is for QA and the human to decide. Emulation was not a problem: the whole run took about
six minutes.

Cleanup: `docker rm -f -v t182-dind` (the container and its anonymous volume only). `docker ps -a` shows no
container. The temporary `.env` is deleted. The dev `infra/.env` (sha1 `714c7630...`), `infra_minio_data`,
`infra_postgres_data` and `infra_redis_data` (creation times) and the whole volume list (sha1) are the same as before the
task.

### L-1

Step 6 table corrected (see above): 0 errors, 97 warnings.

### PLAN-002 1.2 (step 5)

Not re-scored. The residual conditions of RISK-012 1.1 and RISK-010 1.5 are recorded as **pending the human's
approval of PLAN-002 1.2 at the CR-002 gate**; PLAN-002 1.2 must be approved before or together with RISK-010 1.5
and RISK-012 1.1. If the human declines it, both risks return to re-score. The fresh amd64 condition of
RISK-012 1.1 ("the fresh amd64 run (AC-9, AC-16)") rests on the run above and on the AC-16 decision.

## Round 3 (Software Developer role, 2026-10-31)

### AC-9 / AC-16: fresh-host amd64 run with the repository smoke script (after TASK-184)

Disposable daemon, new and empty: `docker run -d --name t184-dind3 --privileged -e DOCKER_TLS_CERTDIR=
docker@sha256:cb160a57fcb936668f8ab8e4a9d73c66b7975226aa87e466233734edbcd83ccc` (arm64 entry of the
`docker:dind` index, as in round 2). `docker info`: `images=0`, `containers=0`, Docker Server 29.9.2, Compose v5.6.1.
Tree: `git archive $(git stash create)` (commit `0716ce7`: HEAD `7351bfb` plus the uncommitted TASK-184 change, since
TASK-184 is not committed yet), extracted in `/work`, `git init` and one commit inside the container so that
`check_image_pins.py` can list files, temporary untracked `infra/.env` (generated keys, `CORS_ORIGINS=[]`, PRB-056) and a
self-signed certificate pair. `apk add bash curl python3 git`. Client and builds with `DOCKER_DEFAULT_PLATFORM=linux/amd64`,
`COMPOSE_PROJECT_NAME=medhub-t184`. The script is the repository's `infra/smoke-test.sh`, sha1 `cf0d9b451f495666dbddf193e1d10d84a2bc7f4a`, identical to the working-tree file.

| Step | Command (inside the daemon container) | Result |
|---|---|---|
| Architecture | `uname -m` in the dind container | `aarch64` (the daemon host; images are amd64 by `DOCKER_DEFAULT_PLATFORM`) |
| Architecture of the stack | `docker compose exec -T <svc> uname -m` for object-store, backend, postgres, redis, reverse-proxy | `x86_64` for all five. `docker image inspect` of the five local images: `amd64` |
| Build | `docker compose build --no-cache --pull` | exit 0, 5 m 17 s |
| Start | `docker compose up -d`, wait 100 s | backend and object-store `healthy`; celery-worker, frontend, postgres, redis, reverse-proxy `Up`; preflight and init `Exited (0)` |
| Pins | `python3 infra/check_image_pins.py` and `python3 -m unittest discover -s infra/tests` | exit 0; 32 tests OK |
| Digests | `docker images --digests --no-trunc` | `chrislusf/seaweedfs` `sha256:f7a49e3f3972ebed5be2ed4befa4a0c68eb7bdddba6e692d42729ceb545134b8`; `postgres` `sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97`; `redis` `sha256:b6b6e3dc0c0952737748e55d5d885272840c7e42ba41ab1d5489f693419882f5`; `nginx` `sha256:e2d97c2b8c016f12c2f1a27d095685063b2f281c4edf2babfde6001cf4fb77a8`; five `medhub-t184-*` local builds (backend, celery-worker, frontend, object-store-init, object-store-preflight), no other image. Each registry image is the pinned digest |
| Smoke | `bash infra/smoke-test.sh` (inside the container) | **`=== Results: 26 passed, 0 failed ===`**, including `[PASS] object-store publishes no host port` |

**N/N: 26/26.** AC-9 and AC-16 are recorded as met on this run (one empty amd64 daemon built, started and
checked the whole stack, the pin check passed, and the unmodified repository script passed every check).
Round 2's 25 of 26 is explained by PRB-059, resolved by TASK-184 (R2 there reproduces 25/1 on the same recipe
before the change and gives 26/26 after).

Caveat for QA: the tree is the uncommitted working tree of TASK-184. Repeat on the committed head if the
reviewer requires it; the script has the same sha1 either way. The archive was streamed with
`COPYFILE_DISABLE=1`: a first attempt without it carried macOS `._*` files into the image (alembic failed on a
null-byte file, `check_image_pins.py` could not read `._ci.yml`); that daemon was discarded and the run above is
the clean rerun, not a script defect.

Cleanup: `docker rm -f -v t184-dind3` (container and its anonymous volume only). `docker ps -a` shows no container.
Dev `infra/.env` sha1 `714c7630...` and the creation times of `infra_minio_data`, `infra_postgres_data`,
`infra_redis_data` (`2026-06-20T17:29:26Z`) are unchanged. TASK-182 stays `in_review`.

## QA review, round 2 (QA engineer, 2026-10-31): APPROVED

Status `in_review` → `approved`. This supersedes "TASK-182 stays `in_review`" in Round 3.

- **H-1 closed.** Round 3 is one run on an empty daemon (`images=0`). It covers the whole stack: build
  `--no-cache --pull`, `up -d` of all services, every service `x86_64`, and the registry images at their
  pinned digests. The pin check passes, and the repository smoke script (sha1 `cf0d9b45...`, the TASK-184
  change) gives `26 passed, 0 failed`. **AC-9 and AC-16 are met.**
  - The daemon host is arm64 with amd64 images (`DOCKER_DEFAULT_PLATFORM`). This is the recipe accepted in round 1.
  - The run used the uncommitted tree. QA checked that the working-tree script has the same sha1, so no
    rerun on the committed head is required.
  - Round 2's 25/26 is fully explained by PRB-059. TASK-184 reproduced it before the fix and passes after.
- **L-1 closed.** The Step 6 table matches QA's parser.
- **PLAN-002 1.2:** QA keeps its round 1 recommendation. The condition stays pending human approval at the
  CR-002 gate. PLAN-002 1.2 must be approved before or together with RISK-010 1.5 and RISK-012 1.1, and if it
  is declined both RISKs go back to re-score. The fresh amd64 evidence condition of RISK-012 1.1 is now met.
- **LOW (not blocking, record text):** Step 5 AC-15 still reads "TS-014 (`approved` 1.4)". TASK-184 bumped it
  to 1.5, and QA approved 1.5 with TASK-184, so AC-15 holds with TS-014 1.5. → Read that line as 1.5. No other
  change is needed.

QA reran these:
- TASK-184 R1 and M1/M3 on Compose v2.20.2 (see TASK-184 "QA review").
- `check_image_pins.py` exits 0, and `infra/tests` passes.
- `traceability-check`, fallback parser over the whole project (380 records): **0 errors**, 97 warnings
  (AC-18). The two extra records since round 1 are TASK-184 and PRB-059.
