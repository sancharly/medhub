---
id: "CR-001"
type: change-request
title: "Pin and review SOUP so the release gate's SOUP check can pass"
status: in_progress
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
branch: "bug/soup-pinning"
links:
  - target: "PRB-001"
    relation: resolves
  - target: "PRB-002"
    relation: resolves
  - target: "PRB-033"
    relation: resolves
  - target: "TASK-154"
    relation: relates_to
  - target: "TASK-155"
    relation: relates_to
  - target: "TASK-156"
    relation: relates_to
  - target: "TASK-157"
    relation: relates_to
  - target: "TASK-158"
    relation: relates_to
  - target: "TASK-159"
    relation: relates_to
  - target: "RISK-010"
    relation: relates_to
  - target: "SR-028"
    relation: relates_to
tags: ["soup", "configuration-management", "regulatory", "class:B", "issue:sancharly/medhub#26"]
---

# CR-001 — Pin and review SOUP

## Reason

The release gate of PLAN-001 requires every SOUP item to carry a unique designation (IEC 62304
§8.1.2) and a dated anomaly-list review no older than 365 days (§7.1.2–7.1.3, §6.1 f). Today no
SOUP item meets the second condition (35 `soup_anomaly_review_stale` warnings in
`docs/reports/gap-report-2026-10-21.md`) and seven fail the first:

- **PRB-001** (major): every container image is referenced by a moving tag (`latest`, `alpine`,
  `16`, `7-alpine`, `3.12-slim`, `20-slim`), so SOUP-001 and SOUP-020..024 cannot state what is
  deployed and the released build is not reproducible (§5.8.5, RR-010).
- **PRB-002** (major): `boto3` is imported by `ObjectStorageClient` but declared in no manifest,
  so attachment storage (SR-013) fails in any environment built from the declared dependencies and
  SOUP-019 has no version.
- **PRB-033** (minor): `fakeredis`, used only by tests, is a runtime dependency and ships in the
  production image as an unreviewed, unused SOUP item (SOUP-018).
- **TASK-154**: the first anomaly-list review of every SOUP item has never been run. It is a
  residual-risk precondition of RISK-010, together with PRB-001.

Source: GitHub issue sancharly/medhub#26.

## Scope

### In scope

1. **Image pinning (PRB-001).** Every container image reference uses tag plus digest
   (`<repository>:<tag>@sha256:<digest>`), where the tag names a full upstream release. Files:
   `infra/docker-compose.yml` (`image:`), `backend/Dockerfile` and `frontend/Dockerfile` (`FROM`, all
   stages). The service containers in `.github/workflows/ci.yml` (`postgres`, `redis`) are pinned
   to the same references as Compose, so verification runs against the shipped SOUP version (see
   Assumption A-2).
2. **Pin check.** A CI job that fails on any Compose `image:` or Dockerfile `FROM` reference
   without an `@sha256:` digest.
3. **SOUP records for the images.** SOUP-001, SOUP-020, SOUP-021, SOUP-022, SOUP-023 and
   SOUP-024: `soup_version` records the release (patch) version; the body records each full image
   reference, digest included, and where it is used.
4. **boto3 (PRB-002).** `boto3` becomes a required runtime dependency in
   `[project] dependencies` of `backend/pyproject.toml` (not an optional extra), `backend/uv.lock`
   is refreshed, SOUP-019 records the locked version, and an automated test instantiates
   `ObjectStorageClient` so a missing SDK fails the build.
5. **fakeredis (PRB-033).** Moved to the `dev` dependency group, lock refreshed, SOUP-018 marked
   `obsolete`.
6. **Anomaly-list review (TASK-154), in full.** Every non-obsolete `soup` record gets a dated,
   sourced review of its published anomaly list for the exact version; hazard-relevant anomalies
   are escalated to RISK records, MedHub-affecting defects to PRBs.
7. **Risk re-assessment (§7.4).** RISK-010 is revised once the controls it assumes exist and are
   verified.
8. **Records.** PRB-001, PRB-002 and PRB-033 move to `resolved` after the fix is verified, each
   with its `## Resolution` written. TS-013 (verifies SR-028) gains the test cases for SR-028 AC-5
   and AC-6.

### Requirements decision

- **SR-028 amended (v1.4 → v1.5, approved 2026-10-22).** RR-008 (exact versions that match the build,
  dated anomaly review) and RR-010 (reproducible build) are realized only by SR-028, but none of
  SR-028's acceptance criteria stated those obligations: its four criteria cover requirement
  records only. The pin check and the anomaly review in this CR would therefore have had nothing
  testable to verify against. SR-028 gains AC-5 (every component resolves to one exact version;
  images pinned by tag and digest; CI fails on an image reference without a digest) and AC-6 (the
  SOUP record version matches the build and carries a dated, sourced anomaly review). Amending was
  preferred to a new SR because SR-028 already carries the whole SOUP trace: it `satisfies` RR-008
  and RR-010, `mitigates` RISK-010, is implemented by TASK-154 and covered by ADD-024 (the CI
  pipeline, where the pin check lives). A new SR would duplicate those links.
- **SR-013 unchanged.** Its AC-3 ("an authorized user can download or open an attachment") is
  already violated by PRB-002; declaring boto3 restores conformance without a new requirement. The
  `ObjectStorageClient` instantiation test is verification evidence for SR-013 AC-3 and SR-028
  AC-5.
- **No new UN, NFR or RR.** RR-008 and RR-010 already state the regulatory obligations with
  clause citations.

### Out of scope

- Upgrading any SOUP item to a newer major or minor version. Pinning records the version in use
  now; an upgrade found necessary by the anomaly review is a separate CR, raised as a PRB.
- Pinning GitHub Actions (`actions/checkout@v4`, `setup-python@v5`, `setup-node@v4`) by commit
  SHA, the `python-version`/`node-version` CI settings, and the unpinned `pip install uv` in
  `backend/Dockerfile`. They are build and verification tooling, not SOUP; tracked as PRB-034.
- Moving the frontend build stage off end-of-life Node 20; tracked as PRB-035.
- A SOUP record for the `node:20-slim` build image. It is pinned like every other image (it is a
  Dockerfile `FROM`), but it only builds the bundle and is not shipped, so under `soup-management`
  it is tooling, not SOUP (Assumption A-3).
- Changing the PRBs' status before the fix is verified.

### Risk impact (§7.4)

`affects_controls`: the change implements two control measures RISK-010 already relies on
(immutable versions; anomaly review) and adds a protective one (the CI pin check). No new hazard is
expected from the change itself. Pinning delays security patches, which RISK-010 already records
as a risk introduced by its controls; the PLAN-002 cadence is the counterweight. Removing
`fakeredis` from the runtime removes the misconfiguration path PRB-033 describes toward RISK-005
and RISK-007. Any hazard-relevant anomaly found by the review is a new input to the Risk stage.

#### Change analysis (Risk stage, 2026-10-22)

Scales and matrix: `docs/medtrace.yml` (5 × 5 `risk_matrix`), PLAN-005. The analysis covers the
four changes of the Scope and the review that follows them. Records consulted: RISK-001,
RISK-005, RISK-007 and RISK-010; ADD-005, ADD-006, ADD-012, ADD-016, ADD-017, ADD-018 and ADD-024;
SOUP-001, SOUP-018..024; TS-001, TS-007, TS-008, TS-011 and TS-013.

**Conclusion.** The classification `affects_controls` is confirmed. The change introduces no new
hazard and does not raise the software safety class: the worst harm reachable through any item
below is that of an existing RISK, severity 3 at most, which class B already covers. No new RISK
record is needed. Two existing records are affected: RISK-010, whose controls the change
implements (AC-14), and RISK-007, whose control "object storage dependency declared" PRB-002's
resolution implements (see Q-3).

| Change (task) | Software items / SOUP | §7.4.1 hazard contribution | §7.4.2 controls affected | §7.4.3 verification |
|---|---|---|---|---|
| Image pinning (TASK-155) | Deployment topology; SOUP-001, 020–024 (ADD-005, 006, 012, 016, 017, 018) | The pin names the image the floating tag resolves to when the pin is made: a patch-level move at most, with the same major.minor line (A-4). On the reference workstation the cache held older patches: nginx 1.31.2 → 1.31.8, Redis 7.4.9 → 7.4.11, PostgreSQL 16.14 → 16.15. Those are the images any `docker compose pull` or CI build already receives. No new hazard. | Implements RISK-010's design control (immutable versions). The controls that run on these images (TLS/HSTS on nginx, SR-001; SSE on MinIO, SR-022; session store on Redis, SR-030) are not changed in configuration. | AC-5 smoke run of the pinned stack; full CI (AC-16), including the TS-011 header tests |
| CI pin check (TASK-156) | SI-DEVINFRA (ADD-024), not deployed | None at runtime. Failure modes: a false negative (an unpinned reference not flagged) is covered by a negative fixture for each reference form. A false positive only blocks a merge. | Adds a protective control to RISK-010 | TS-013 TC-013.5, TC-013.6 |
| boto3 required (TASK-157) | SI-ATTACH (ADD-012); SOUP-019 with its transitives `botocore`, `s3transfer`, `jmespath` | Restores SR-013 AC-3 and adds no new failure path. The attachment write path now reaches MinIO in a real deployment, so the `ServerSideEncryption="AES256"` request runs live for the first time. If MinIO's KMS is misconfigured, MinIO rejects the request and the upload fails loudly (availability, RISK-007). The object is never stored silently in plaintext. | **RISK-007** control "Object storage dependency declared and verified at startup" is realized as *declared as a required dependency and verified in CI* (instantiation test, production-image import check), not by a check at application start. Assessed as equivalent for the cause it targets (a missing SDK), because the shipped image is built only from the frozen lock. RISK-007's residual (3 × 2, `alarp`, set by the single-host decision ADR-0010) is unchanged. | TS-007 TC-007.5, TS-013 TC-013.7, TC-013.8 |
| fakeredis to dev (TASK-158) | Backend runtime image; SI-AUTH `U-AUTH-Session` (ADD-006) indirectly; SOUP-018 | Removes an unused component from the product. No application module imports it, and no control of RISK-005 or RISK-007 depends on it. The misconfiguration path it removes: one in-process FakeRedis per gunicorn worker loses every session on restart (RISK-007), and a session revoked on one worker stays valid on the others, which defeats SR-030 revocation (RISK-005). After the change, that wiring fails at import in the production image. Tests keep it through the dev group, so TS-001's environment is unchanged. | None weakened. RISK-005 (residual P = 1) and RISK-007 are not re-scored. | TS-013 TC-013.8 (absence in the production image); backend suite |
| Anomaly review (TASK-154) | All non-obsolete SOUP | The review introduces nothing itself. Its findings are new inputs to this stage (AC-12). | Implements RISK-010's protective control | Dated reviews in the SOUP records; TS-013 TC-013.9 |

**Observation passed to TASK-154 (D-4).** On 2026-10-22, `docker buildx imagetools inspect`
resolved every other image normally but refused `minio/minio:latest` and `minio/mc:latest` on
Docker Hub ("pull access denied, repository does not exist or may require authorization"). The
`quay.io/minio/*` equivalents returned 401. The workstation's cache holds
`RELEASE.2025-09-07T16-13-09Z` (server) and `RELEASE.2025-08-13T08-35-41Z` (client), arm64 only,
which TASK-155 pins. The condition predates this CR: the floating tag cannot be pulled either.
Pinning makes it visible but does not cause it. The consequences, if the vendor confirms the
distribution change:
- a fresh or amd64 host cannot obtain the object store (§5.8.5; availability, RISK-007);
- the SSE server receives no upstream fixes (RISK-001 through RISK-010's "risks introduced by
  controls").

Neither consequence exceeds class B. TASK-154 confirms the status from the vendor's own notices and
escalates it, without changing the component.

**Verification gap noted (outside this CR).** No test verifies that an attachment written through
`ObjectStorageClient` is stored with SSE-AES256 by a real MinIO. The unit tests assert only that a
mocked `put_object` is called, and TS-008 covers field encryption, not object storage. Until
PRB-002 is fixed the path never ran in a deployment, so the gap was latent. It concerns RISK-001's
at-rest control (SR-022) and is proposed as a PRB (Q-4).

**RISK-010 residual.** Probability 1 holds once TASK-154..158 land. No re-score is recommended.
Rationale:
- The sequence of events starts with "a floating image tag or an unreviewed library upgrade
  pulls a new version". After this CR, every shipped component is fixed by a committed lock file
  or an image digest. A new version therefore needs a commit that changes the lock or the digest,
  and that commit passes PR review, the pin check and the PLAN-002 rule "review at every
  dependency change".
- The anomaly review gives each pinned version a dated, sourced baseline.
- What remains unenforced is process: no automated gate ties a lock or digest change to a SOUP
  record update. It is checked by review and by TS-013 TC-013.9 / `traceability-check` at release.
  That is consistent with Improbable for class B.
- PRB-034 (unpinned CI tooling, unpinned `uv`) and PRB-035 (Node 20 build stage) do not reopen
  the path: `uv sync --frozen` and `npm ci` install only locked versions, and neither tool ships.
- Severity stays 3, so the matrix derives 3 × 1 → `acceptable`.

The score is conditional on TASK-154 finding no hazard-relevant, unfixed anomaly in a
control-bearing item. If it finds one, TASK-159 re-scores with that rationale. Acceptance is the
human's, through the approval of the revised RISK-010.

## Acceptance criteria

Pinning (PRB-001)

- **AC-1:** Every `image:` in `infra/docker-compose.yml` and every `FROM` in `backend/Dockerfile`
  and `frontend/Dockerfile` that names an image has the form `<repository>:<tag>@sha256:<64 hex>`.
  The `<tag>` names a full upstream release: major.minor.patch for semver-versioned images (for
  example `nginx:1.27.3-alpine`), the `RELEASE.<timestamp>` tag for MinIO images. No reference
  uses `latest` or a tag without a patch component.
- **AC-2:** Where one SOUP item is referenced more than once (Python: builder and runtime stages;
  nginx: reverse proxy and frontend runtime stage), every reference uses the identical tag and
  digest. The `services.*.image` entries in `.github/workflows/ci.yml` use the same tag and digest
  as the matching Compose service.
- **AC-3:** A CI job runs on every pull request and fails, naming the file and line, when any
  Compose `image:`, Dockerfile `FROM` or `.github/workflows/*.yml` `services.*.image` image
  reference lacks `@sha256:<64 hex>`. It passes on the
  repository after AC-1. A `FROM` that names an earlier build stage, or `FROM scratch`, is not
  flagged. Evidence: the check run against an unpinned reference (fixture or temporary edit) exits
  non-zero; run against the repository it exits zero.
- **AC-4:** `soup_version` of SOUP-001, SOUP-020, SOUP-021, SOUP-022, SOUP-023 and SOUP-024 equals
  the release version in the pinned tag (for example `1.27.3`), and each record's body lists every
  full image reference with its digest and the file that uses it. The "Floating tag (PRB-001)"
  notes are gone.
- **AC-5:** The pinned stack still works: `docker compose -f infra/docker-compose.yml build`
  succeeds, the stack starts, and `infra/smoke-test.sh` passes against it.

boto3 (PRB-002)

- **AC-6:** `boto3` appears under `[project] dependencies` in `backend/pyproject.toml` (not in a
  dependency group, not an optional extra), `backend/uv.lock` resolves it to exactly one version,
  and `uv lock --check` succeeds. SOUP-019's `soup_version` equals the locked `boto3` version, and
  its body records the locked `botocore` version.
- **AC-7:** An automated backend test, run in CI on every pull request, instantiates
  `ObjectStorageClient` from the test settings without stubbing or patching the `boto3` import,
  and fails when `boto3` cannot be imported. The test needs no reachable object-storage endpoint.
- **AC-8:** In an environment installed with `uv sync --frozen --no-dev` (the production
  dependency set used by `backend/Dockerfile`), `import boto3` succeeds.

fakeredis (PRB-033)

- **AC-9:** `fakeredis` is absent from `[project] dependencies` and present in the `dev`
  dependency group, `backend/uv.lock` is refreshed, and an environment installed with
  `uv sync --frozen --no-dev` does not contain `fakeredis`.
- **AC-10:** SOUP-018 has `status: obsolete`, a bumped `version` and a change-log entry citing
  PRB-033 and CR-001.

Anomaly-list review (TASK-154)

- **AC-11:** Every `soup` record whose status is not `obsolete` has an `anomaly_review` date, and
  its "Anomaly list review" section cites each source actually checked (advisory database, vendor
  security page or release notes, by name and URL) for its exact `soup_version`. It lists every
  anomaly found that applies to that version with a hazard-relevance judgement, or states "none
  found". No section still reads "Not yet performed". The image items (SOUP-001, SOUP-020..024)
  are reviewed against the version pinned under AC-4, not the former floating tag.
- **AC-12:** Every anomaly judged hazard-relevant is recorded in a RISK record (new, or an
  existing one revised) that links `relates_to` → the SOUP record, and every anomaly that affects
  MedHub's behaviour has a PRB. This CR's body lists each escalation, or states that there were
  none.
- **AC-13:** PLAN-002's "SOUP monitoring" section matches the cadence and owner actually applied
  in the review, or is revised to match.

Risk (RISK-010)

- **AC-14:** RISK-010 is revised. Its control table names the implementing record and the
  verification evidence for "every image and dependency pinned" (CR-001, the AC-3 check, TS-013)
  and for "anomaly and advisory review" (TASK-154, the dated SOUP reviews). The residual
  probability is confirmed at 1, or re-scored against `risk_matrix` with a rationale, and
  `acceptability` is derived from the scores. The residual-risk text no longer states the PRB-001
  and TASK-154 preconditions as unmet. Its `relates_to` link to the obsolete SOUP-018 is removed.

Verification and records

- **AC-15:** TS-013 contains test cases, with expected results, for SR-028 AC-5 and AC-6, and
  still `verifies` SR-028.
- **AC-16:** All jobs in `.github/workflows/ci.yml`, including the new pin check, pass on the
  branch head. The backend test suite (`pytest`) and the frontend test suite pass locally.
- **AC-17:** PRB-001, PRB-002 and PRB-033 are `resolved`, each with a `## Resolution` that names
  the changed files and the reproducible verification, and each has an incoming `resolves` link
  from this CR.
- **AC-18:** `traceability-check` over the whole project reports 0 errors and no
  `soup_anomaly_review_stale` warning for any non-obsolete SOUP record. Every record created or
  changed by this CR is `in_review`, or `obsolete` for SOUP-018.

## Verification approach

IEC 62304 §8.2.1 (change approval) and §8.2.3 (verification of changes).

- **Static checks (AC-1, AC-2, AC-4, AC-6, AC-9):** inspection of the changed files against the
  criteria, plus the pin check (AC-3) and `uv lock --check`, all in CI.
- **Pin check (AC-3):** a negative test with an unpinned reference and a positive run on the
  repository, both recorded in TS-013.
- **Runtime dependency set (AC-7, AC-8, AC-9):** the `ObjectStorageClient` instantiation test in
  the backend suite, plus a check against a `--no-dev` environment (the built backend image or an
  equivalent `uv sync --frozen --no-dev`). The architect decides whether that check runs in CI or
  once, recorded in the test report.
- **Integration (AC-5):** a Compose build and start of the pinned stack with `infra/smoke-test.sh`,
  run on the branch.
- **Regression (AC-16):** the full CI pipeline on the branch head.
- **Anomaly review (AC-11..AC-13):** a human reviews each `soup` record's review section and its
  cited sources during approval of the records.
- **Records (AC-14, AC-15, AC-17, AC-18):** `traceability-check`; human approval of SR-028,
  RISK-010, the SOUP records and TS-013.

Results go into the next test report (TR) for the release.

## Assumptions

- **A-1:** `soup_version` holds the release version only (for example `1.27.3`). The digest, which
  is the immutable designation, is recorded in the SOUP body (decision 1 of the issue). For MinIO
  images the release version is the `RELEASE.<timestamp>` tag, because MinIO publishes no semver
  patch version.
- **A-2:** "Every image reference uses tag plus digest" includes the CI service containers in
  `.github/workflows/ci.yml`, so tests run against the shipped versions, and the pin check scans
  the workflow files too (Decision D-1).
- **A-3:** The `node:20-slim` build stage is pinned but gets no SOUP record, because it is not
  shipped (`soup-management`: development tooling that is not shipped is not SOUP). This matches
  how the SOUP list already treats Vite, TypeScript and the test runners.
- **A-4:** Pinning records the version in use when the change is made. No component is upgraded
  by this CR.
- **A-5:** Each image's base OS (Debian for `python:*-slim` and `postgres`, Alpine for the
  `*-alpine` images) is covered by the image's own SOUP record, identified by the digest, and named
  in that record's environment section. It is not a separate SOUP record.

## Decisions

Approved with this CR by Carlos Santiago Liceras on 2026-10-22.

- **D-1:** The pin check also scans `.github/workflows/*.yml` `services.*.image` (AC-3).
- **D-2:** Unpinned CI and build tooling (GitHub Actions tags, `python-version`/`node-version`,
  `pip install uv`) is raised as PRB-034 and is not fixed by this CR.
- **D-3:** Node 20 end of life (2026-04-30) is raised as PRB-035 and is not fixed by this CR;
  `node:20-slim` is still pinned here like every other image.
- **D-4:** MinIO community distribution status is confirmed or refuted by TASK-154 from the
  vendor's own notices; if confirmed it is escalated under AC-12. The component is not changed by
  this CR.
- **D-5:** The branch is renamed to `bug/soup-pinning` to match PLAN-003's branch prefixes.

## Implementation plan

The plan is the TASK records below (overlay: no `docs/plans/<feature>.md`). Each task resolves its
own PRB. All tasks are on `bug/soup-pinning`, one commit per QA-approved task with its records.

| Order | Task | CR-001 AC | Depends on | Size |
|---|---|---|---|---|
| 1 | [TASK-155](../design-outputs/tasks/TASK-155-pin-container-images-by-tag-and-digest.md) Pin every container image by release tag and digest | AC-1, AC-2, AC-4, AC-5 | none | M |
| 2 | [TASK-156](../design-outputs/tasks/TASK-156-ci-image-pin-check.md) CI check that rejects image references without a digest | AC-3, AC-15 (part), AC-17 (PRB-001) | TASK-155 | M |
| 3 | [TASK-157](../design-outputs/tasks/TASK-157-declare-boto3-required-runtime-dependency.md) Declare boto3 as a required runtime dependency | AC-6, AC-7, AC-8, AC-15 (part), AC-17 (PRB-002) | none (parallel with 1–2) | M |
| 4 | [TASK-158](../design-outputs/tasks/TASK-158-move-fakeredis-to-dev-dependency-group.md) Move fakeredis to the dev dependency group | AC-9, AC-10, AC-15 (part), AC-17 (PRB-033) | TASK-157 (same files) | S |
| — | **Checkpoint A** after tasks 1–4 | — | — | — |
| 5 | [TASK-154](../design-outputs/tasks/TASK-154-soup-anomaly-list-review.md) First SOUP anomaly-list review (revised, v1.3) | AC-11, AC-12, AC-13 | TASK-155, TASK-157, TASK-158 | L (records only) |
| 6 | [TASK-159](../design-outputs/tasks/TASK-159-reassess-risk-010-and-verify-cr-001.md) Re-assess RISK-010 and verify CR-001 end to end | AC-14, AC-15, AC-16, AC-18 | all above | S |

Every AC-1..AC-18 is covered. AC-15 is built up by tasks 2–4 (TC-013.5..8) and completed in
task 6 (TC-013.9). AC-16 is run by every task and confirmed on the branch head in task 6.

**Checkpoint A (after TASK-155..158).** All CI jobs are green on the branch head, the new
`image-pins` job included. `uv lock --check` passes. The backend suite passes with coverage
≥ 85 %, and the frontend suite passes. The pinned stack builds, starts and passes
`infra/smoke-test.sh`. `traceability-check` shows no errors for the touched records; only the
expected RISK-010 → SOUP-018 warning remains. TASK-154 starts only after this checkpoint, so it
reviews the final versions.

**Plan-stage decisions.**
- The `--no-dev` check (AC-8, AC-9) runs **in CI on every pull request**, as a step of the Docker
  Build job against the built backend image (TASK-157, extended by TASK-158).
- The pin check is a standard-library Python script (`infra/check_image_pins.py`) with `unittest`
  fixtures: no new SOUP or tooling, and no YAML parser.
- ADD-024 is updated because `U-INF-CIPipeline` gains two checks (TASK-156, TASK-157/158).
- No ADR: the design decision is this CR's Decisions, and the change adds no new architectural
  element.
- No other ADD changes: SOUP-018 has no inbound ADD link, and SOUP-019's user ADD-012 is unchanged
  in design.
- Record convention: a record changed by several tasks of this CR is bumped **once**, by the first
  task that touches it. Its approval record is cleared then, and later tasks extend the same
  version-history entry. This applies to the SOUP records, TS-013 and ADD-024.

### Risks

| Risk | Impact | Mitigation |
|---|---|---|
| A registry digest changes between the plan and the build, or the floating and full-release tags carry different index digests: on 2026-10-22 `nginx:alpine` and `nginx:1.31.8-alpine` had the same image config but different digests | Pinned digest differs from the plan table | Pin the **full-release tag's** index digest, check that its per-platform config reports the same version, and record the date and command in the SOUP record. Once pinned, later drift no longer matters. |
| MinIO images can no longer be pulled (D-4) | AC-5 is reproducible only on a host with the cached images. The cached images are arm64 only, and their digests cannot be checked against a registry. | Pin the cached RepoDigest and say so in SOUP-022/023. CI does not use MinIO. TASK-154 confirms the status and escalates it (PRB, RISK-007/RISK-010 input). Q-2. |
| `uv lock` re-resolves unrelated packages when boto3 is added or fakeredis is moved | Unreviewed upgrades, against A-4 | `uv lock` without `--upgrade`. Check the lock diff, and revert any version change other than the added SDK packages. |
| PostgreSQL 16.14 → 16.15 on an existing `postgres_data` volume (reference workstation) | Start-up failure of the pinned stack | A minor release in the same major needs no dump or restore. The AC-5 smoke run covers it. |
| Pinning freezes security patches | Known anomalies stay deployed | PLAN-002 cadence; TASK-154 baseline. Already recorded in RISK-010 "Risks introduced by controls". |
| Interim traceability warning: RISK-010 links the obsolete SOUP-018 between TASK-158 and TASK-159 | Checkpoint A shows a warning | Expected. The link is removed once, in TASK-159. |
| TASK-154 covers 34 records | Shallow or uneven review | Control-bearing items first. Each record is self-contained and approved individually by the human, with its cited sources. |
| A pinned EOL Node 20 build stage (PRB-035) | Build chain frozen on an unsupported runtime | Accepted per D-3; tracked by PRB-035. |

### Plan decisions

Plan approved by Carlos Santiago Liceras on 2026-10-22, with these answers:

- **Q-1:** pin the release each floating tag resolves to in the registry now (patch-level moves
  for nginx, Redis and PostgreSQL against the workstation cache are accepted).
- **Q-2:** pin the cached MinIO releases; AC-5 is accepted as reproducible only on a host holding
  them until TASK-154 settles D-4.
- **Q-3:** TASK-157 updates RISK-007's control row (implementer and verification evidence).
- **Q-4:** the missing end-to-end SSE-AES256 check is raised as PRB-036, outside this CR.

## Version history

- 1.1 (2026-10-22) — Risk stage: change analysis added under "Risk impact (§7.4)". Plan stage:
  implementation plan (TASK-155..159, TASK-154 revised), checkpoint, risks and open questions;
  `relates_to` links to TASK-155..159.
- 1.2 (2026-10-22) — Plan approved; open questions Q-1..Q-4 answered under "Plan decisions";
  PRB-036 raised for Q-4.
