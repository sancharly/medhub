---
id: CR-003
type: change-request
title: Upgrade end-of-life and advisory-affected SOUP, and drop an unused SOUP item
status: in_progress
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-10-29"
updated: "2026-10-30"
branch: bug/soup-upgrades
risk_impact: affects_controls
links:
  - target: TASK-161
    relation: relates_to
  - target: TASK-162
    relation: relates_to
  - target: TASK-163
    relation: relates_to
  - target: TASK-164
    relation: relates_to
  - target: TASK-165
    relation: relates_to
  - target: TASK-166
    relation: relates_to
  - target: TASK-167
    relation: relates_to
  - target: TASK-168
    relation: relates_to
  - target: RISK-011
    relation: relates_to
  - target: PRB-045
    relation: resolves
  - target: PRB-035
    relation: resolves
  - target: PRB-047
    relation: resolves
  - target: PRB-044
    relation: resolves
  - target: CR-001
    relation: relates_to
  - target: SR-028
    relation: relates_to
  - target: RISK-010
    relation: relates_to
  - target: ADD-023
    relation: relates_to
  - target: SOUP-003
    relation: relates_to
  - target: SOUP-011
    relation: relates_to
  - target: SOUP-019
    relation: relates_to
  - target: SOUP-021
    relation: relates_to
tags:
  - soup
  - maintenance
  - configuration-management
  - class:B
  - issue:sancharly/medhub#32
---

# CR-003 — Upgrade end-of-life and advisory-affected SOUP

## Reason

The first SOUP anomaly-list review (CR-001, TASK-154, 2026-10-22) and CR-001's Specify stage
found four maintenance defects. CR-001 left them out of scope because pinning upgrades nothing
(CR-001 A-4). All four are `minor`, and none is hazard-relevant today, but each one keeps
MedHub on a component that is out of upstream support, exposed to a published advisory, or
recorded wrongly (IEC 62304 §6.1 f, §7.1.2–7.1.3, §8.1.2):

- **PRB-045** (minor, **deadline**): the pinned Redis image
  (`redis:7.4.11-alpine@sha256:892022f9…eab1`, SOUP-021) is built on Alpine Linux 3.21. That
  branch's upstream support ends on **2026-11-01**, three days after this CR is opened. After
  that date the base OS gets no security fixes.
- **PRB-035** (minor): the shipped frontend bundle is built on Node 20, which reached end of life
  on 2026-04-30. Node 20 is used in the `frontend/Dockerfile` build stage and in the CI frontend
  jobs.
- **PRB-047** (minor): `backend/uv.lock` resolves anyio 4.14.0 (SOUP-003), urllib3 2.7.0
  (SOUP-019) and cryptography 49.0.0 (SOUP-011). Each carries published advisories, and all of
  them are fixed upstream. None reaches MedHub's use today.
- **PRB-044** (minor): `openapi-fetch` (SOUP-033) is declared as a runtime dependency but never
  imported. ADD-023 and the arc42 text describe MedHub's API client as generated, when only its
  types are. ADD-004, now obsolete, has the same error.

One CR bundles them, as CR-001 did, for three reasons. They come from the same review. They touch
the same records: the SOUP list, RISK-010 and the SR-028 verification. And they share one
verification run: the pin check, the lock check, the smoke test, both suites and
`traceability-check`. PRB-045's deadline is handled by doing it first (see "Scheduling").

Source: GitHub issue sancharly/medhub#32.

## Scope

### In scope

1. **Redis image (PRB-045).** Move the `redis` service in `infra/docker-compose.yml` and the
   `backend-tests` service container in `.github/workflows/ci.yml` to one Redis 7.4.x image
   built on a supported base OS, pinned by release tag and digest. Upstream builds Redis 7.4 on
   Alpine 3.21 only, so the image is the official Debian 12 (`-bookworm`) variant (D-1).
   Update SOUP-021 and review its anomaly list at the new version, base-OS packages included.
2. **Node build runtime (PRB-035).** Move the `frontend/Dockerfile` build stage to a supported
   Node LTS line, pinned by release tag and digest. Move the `node-version` of the CI
   `frontend-quality` and `frontend-tests` jobs to the same major line, and the `openapi-lint`
   job too if Q-3 is accepted. Update the verification-environment line of TS-001..TS-013. The
   build image stays tooling, not SOUP (A-3).
3. **Python transitives (PRB-047).** Refresh `backend/uv.lock` for anyio, urllib3 and
   cryptography only. Update SOUP-003, SOUP-011 and SOUP-019 and review each one's anomaly list
   at the new versions. Add a known-answer test that proves field ciphertexts written under
   cryptography 49.0.0 still decrypt (Q-4). Correct the body of RISK-011, which names
   cryptography 49.0.0 as the version in use (`RISK-011-encryption-key-management-failure.md:55`;
   human decision, 2026-10-29).
4. **openapi-fetch (PRB-044).** Remove the package from `frontend/package.json` and
   `frontend/package-lock.json`, set SOUP-033 `obsolete`, and remove the `relates_to` → SOUP-033
   links from ADD-023 and RISK-010. Correct the description of SI-FE-APICLIENT in ADD-023 and in
   the arc42 sections and PlantUML diagram that repeat it. Add a correction note to the obsolete
   banner of ADD-004.
5. **Risk (§7.4).** Run a change analysis over the four changes and every RISK record that
   considers SOUP-003, 011, 019, 021 or 033. Revise RISK-010 for the removed SOUP-033 link and
   for its PRB-035 rationale.
6. **Records.** PRB-045, PRB-035, PRB-047 and PRB-044 move to `resolved` once their fixes are
   verified, each with its `## Resolution`. TS-008 gains the known-answer test case.

### Scheduling

PRB-045 goes first. Its task is ordered before all others, and it depends on none of them, so it
can be committed as soon as QA approves it. Even so, the stack will run on Alpine 3.21 after
2026-11-01 unless the whole CR merges before then (see Q-1). No release exists, and none is made
before CR-002 (human decision, 2026-10-22). So for those days the unsupported base OS is used
only in development, CI and pre-release environments. No released product contains it.

### Requirements decision

- **No UN, NFR, RR or SR is created or amended.** SR-028 already states what this change has to
  satisfy again at the new versions. AC-5 requires one exact version per component, images
  pinned by tag and `@sha256:` digest, and a CI check that enforces the digest. AC-6 requires a
  `soup_version` that matches the build and a dated, sourced anomaly review. CR-001 amended
  SR-028 because no criterion stated these obligations. Here they are stated and verified by
  TS-013 TC-013.5..9, so this CR re-runs that verification and changes no requirement.
- **"A SOUP item is in upstream support" is not made an SR.** It is a maintenance-process
  obligation (§6.1 f: evaluating upgrades, patches and obsolescence), so it belongs in PLAN-002,
  not in a product requirement that tests could verify against the software. PLAN-002 has no
  such criterion, which is the shared root cause of PRB-045 and PRB-035. Q-5 asks whether to fix
  that here.
- **The SRs whose controls run on the upgraded SOUP stay unchanged:** SR-022 (field encryption,
  cryptography), SR-030 (session store, Redis), SR-031 (CSRF and security headers, Starlette and
  anyio; the client side built by Node) and SR-013 (attachments, urllib3 under boto3). The change
  must keep them conforming, and the regression suites and AC-9 verify that.
- **The ADD-023 correction is a description fix.** It makes the design record match the code.
  SR-031, which ADD-023 implements, does not change.
- **RR-008 and RR-010 stay unchanged.** Their obligations (exact versions, dated review,
  reproducible build) are met again through SR-028.

### Out of scope

- Moving Redis to another minor or major version (8.x). That changes the licence terms and the
  server's behaviour, so it needs the human's decision and its own analysis (see Boundaries).
- PRB-034: pinning GitHub Actions by commit SHA, pinning `python-version` and `node-version` to a
  patch, and the unpinned `pip install uv`. This CR changes only the Node **major** line in CI.
- Upgrading any other locked package, npm dependency or image. The lock diffs are limited to what
  AC-7 and AC-10 name.
- CR-002 (the MinIO replacement and hardening, PRB-042 and PRB-043) and its RISK-012 controls.
- A SOUP record for the Node build image (A-3).
- Adding an `engines` field or an `.nvmrc` to the frontend. The PRB-035 investigation observed
  the gap, but nothing in this CR's scope needs it.
- Changing TP-001, TR-001 or TR-002. They are evidence of past runs on Node 20 and keep their
  content.
- Changing the PRBs' status before their fixes are verified.

### Boundaries

- **Ask first:** if no Redis 7.4.x image exists on a qualifying Alpine branch (AC-2), stop and ask
  before choosing another variant or version. *This happened at the Plan stage on 2026-10-29. The
  human chose the Debian 12 variant (D-1), and AC-1 and AC-2 were amended to match.* Also ask first before any lock change beyond AC-7
  or AC-10, and before any change to a `pyproject.toml` floor that is not needed for AC-7.
- **Never:** edit an `approved` record without bumping its version and clearing its approval
  record. Never set a record `approved`.

### Risk impact (§7.4)

Preliminary classification: **`affects_controls`**. All four changes replace or remove SOUP that
existing risk controls run on, or that builds them. The change is meant to add no hazard and does
not raise the software safety class: Redis stays on 7.4 and every other upgrade is a patch or
minor release of the same component. The Risk stage confirms or revises this classification. The
detailed change analysis table is the architect's. The items each change touches are:

| Change | PRB | SOUP / software items touched | Records that consider them |
|---|---|---|---|
| Redis image on a supported base OS (Debian 12, D-1) | PRB-045 | SOUP-021. Deployment topology (`infra/docker-compose.yml` `redis`, AOF persistence on the `redis_data` volume). SI-AUTH `U-AUTH-Session` (ADD-006, SR-030). SI-WORKER broker (ADD-017). SI-DEVINFRA CI service container (ADD-024) | RISK-005, RISK-007, RISK-009, RISK-010 |
| Node LTS for the build stage and CI | PRB-035 | Not SOUP (A-3). SI-DEVINFRA `U-INF-Toolchain` and `U-INF-CIPipeline` (ADD-024). The bundle it builds carries the client-side controls of SI-FE-APICLIENT (ADD-023, SR-031) and the SI-FE-* items | RISK-005 (CSRF client side), RISK-010 (path-1 rationale names PRB-035) |
| cryptography 50.0.x | PRB-047 | SOUP-011 with its bundled OpenSSL and cffi. SI-PERSIST crypto (ADD-016, SR-022). ADD-006 | RISK-011, RISK-001, RISK-010 |
| anyio ≥ 4.14.2 | PRB-047 | SOUP-003 (transitive of Starlette). SI-API middleware chain (ADD-005; `SecurityHeadersMiddleware`, `CsrfEnforcementMiddleware`) | RISK-001, RISK-005, RISK-010 |
| urllib3 ≥ 2.8.0 | PRB-047 | SOUP-019 (transitive of botocore). SI-ATTACH object-storage path with the SSE request (ADD-012, SR-013, SR-022) | RISK-007, RISK-011, RISK-010 |
| openapi-fetch removed | PRB-044 | SOUP-033. SI-FE-APICLIENT (ADD-023), no runtime change because the package is not in the bundle | RISK-010 (link removed) |

Points the Risk stage has to settle:

- whether field values encrypted under cryptography 49.0.0 still decrypt under 50.0.x (data
  integrity of PHI at rest), which AC-9 verifies;
- whether the Redis AOF file on an existing `redis_data` volume loads under the new image. The
  data held is sessions and task queue state, not PHI.
- whether the patch releases change any behaviour the controls rely on, judged from each
  upstream changelog.

#### Change analysis (Risk stage, 2026-10-29)

Scales and matrix: `docs/medtrace.yml` (5 × 5 `risk_matrix`), PLAN-005. The analysis covers the
six changes of the Scope at the versions selected below ("Selected versions"), and the anomaly
reviews that follow them.

- Records consulted:
  - every RISK record linked to SOUP-003, 011, 019, 021 or 033: RISK-001 (SOUP-003),
    RISK-005 (SOUP-003, SOUP-021), RISK-007 (SOUP-019, SOUP-021), RISK-009 (SOUP-021),
    RISK-010 (all) and RISK-011 (SOUP-011, SOUP-019);
  - ADD-005, ADD-006, ADD-012, ADD-016, ADD-017, ADD-023, ADD-024;
  - SOUP-003, 011, 019, 021, 033;
  - TS-001, TS-007, TS-008, TS-011, TS-013;
  - PRB-036 (no end-to-end SSE verification).
- Upstream sources, read 2026-10-29:
  - Redis 7.4.12 release notes (github.com/redis/redis/releases/tag/7.4.12);
  - cryptography `CHANGELOG.rst` 50.0.0–50.0.2 (github.com/pyca/cryptography);
  - anyio `docs/versionhistory.rst` 4.14.1–4.14.2 (github.com/agronholm/anyio);
  - urllib3 `CHANGES.rst` 2.8.0 (github.com/urllib3/urllib3);
  - the Node.js release schedule (github.com/nodejs/Release).

**Conclusion.** The classification `affects_controls` is confirmed.

- **No new hazard, class B unchanged.** The worst harm any item below can reach is already in an
  existing RISK, at severity 3 at most. The worst case is PHI at rest becoming unreadable after
  the cryptography upgrade, which is RISK-011's "old rows fail to decrypt". Class B already covers
  that harm, so no new RISK record is needed.
- **Every change keeps a control running on changed SOUP or tooling, and weakens none:**
  - RISK-005: session store and CSRF;
  - RISK-007 and RISK-009: Redis availability and the broker;
  - RISK-001 and RISK-011: field encryption and the SSE request path;
  - RISK-010: pinning and review, which the change implements again at the new versions.
- **Records revised:**
  - RISK-010 is revised now (AC-15, version 1.4, `in_review`).
  - RISK-011 gets a body correction in TASK-163. Its scores do not change.
  - RISK-001, RISK-005, RISK-007 and RISK-009 are not re-scored and are not edited: their bodies
    name no replaced version.
- **Condition.** The conclusion holds unless a new anomaly review (AC-14) finds a hazard-relevant,
  unfixed anomaly at a new version. That would be a new input to this stage, recorded under
  "Escalations" below.

| Change (task) | Software items / SOUP | §7.4.1 hazard contribution | §7.4.2 controls affected | §7.4.3 verification |
|---|---|---|---|---|
| Redis `7.4.11-alpine` (Alpine 3.21) → `7.4.12-bookworm` (Debian 12) (TASK-161) | SOUP-021; deployment topology (`redis` service, AOF on the `redis_data` volume); SI-AUTH `U-AUTH-Session` (ADD-006, SR-030); SI-WORKER broker (ADD-017); SI-DEVINFRA CI service container (ADD-024) | **Server.** Patch release in the same 7.4 line. 7.4.12 (2026-10-26) has one security fix, a heap overflow when a PUBLISH message over 4 GB is propagated over the cluster bus. Cluster mode is off, so the fixed path cannot be reached. No command semantics change, so key TTL, `DEL`, `SET EX` and the list operations Celery uses behave as before. **Base OS.** musl/busybox → glibc/Debian userland, built by upstream from the same Redis source. The image is larger (disk only) and has more packages (`bash`, `apt`, coreutils), so more base-OS CVEs can apply. The AC-14 review covers every installed source package. Debian 12 is past regular security support (2026-07-11) and in Debian LTS until 2028-06-30 (D-1). Debian LTS does not cover every package, so the review also checks `debian-security-support`'s list of packages with limited or no support. **Data.** Same uid 999 for `redis` in both images; the group changes from gid 1000 to 999. The entrypoint chowns `/data` to the `redis` user, so an existing AOF stays readable. The AOF format does not change within 7.4 (A-5). Redis holds sessions and queue state, not PHI, so the worst outcome of a failed load is lost sessions (users log in again) or lost queued notifications. Those are RISK-007 and RISK-009, already scored. No new hazard. | RISK-005: SR-030 session TTL and revocation are MedHub code over unchanged Redis semantics. RISK-007 and RISK-009: availability and the broker, with restart policy and healthcheck unchanged. RISK-010: re-implements "pinned + reviewed" at the new version. None weakened, none re-scored. | The backend suite does not exercise the server: TS-001's unit and service tests use fakeredis, and no test connects to the CI service container. The real-server evidence therefore comes from the Compose stack (TASK-161): the existing-volume load check, `INFO server` and `INFO persistence`, and a session round trip through the proxy. The round trip is login, an authenticated request, logout, then the same cookie rejected (SR-030 revocation). Plus smoke 17/17 (AC-17), whose login check needs Redis for the lockout counter, `/etc/os-release` read from the image (AC-2) and the SOUP-021 review (AC-14). This test gap predates the change, so it is noted, not raised: TS-001 states the fakeredis environment |
| Node 20 → Node 24 LTS for the build stage and CI; `setup-node` in `openapi-lint` (TASK-162) | Not SOUP (A-3). SI-DEVINFRA `U-INF-Toolchain`, `U-INF-CIPipeline` (ADD-024). The bundle it builds carries SI-FE-APICLIENT (ADD-023, SR-031.3) and the SI-FE-* items | Node runs the locked build tools (Vite 5.4.21, esbuild, TypeScript 5.9.3). It is not in the shipped image. `npm ci` installs the same locked, integrity-checked versions, and AC-5 checks that the lock is unchanged. Every locked toolchain package declares a `node` engine range that includes 24. A behaviour difference would show in the emitted bundle, which is covered by the frontend suite running on Node 24 and by the image build. `openapi-lint` stops depending on the runner's default Node. No new hazard. | RISK-005 client-side CSRF header (`withCsrf`, SR-031.3): code unchanged, re-verified by the frontend suite on Node 24. RISK-010: the path-1 rationale no longer cites PRB-035 as open. | Frontend suite and lint/typecheck on Node 24 in CI (AC-18). `npm ci && npm run build` in the CI `build` job (AC-5). Lock diff empty (AC-5). Smoke 17/17: the SPA is served through the proxy (AC-17) |
| cryptography 49.0.0 → 50.0.2 (TASK-163) | SOUP-011 with cffi 2.0.0 and its bundled OpenSSL; SI-PERSIST `U-PER-Crypto` (ADD-016, SR-022). It is the only dependent in the lock (`medhub-backend`) | MedHub uses only `AESGCM.encrypt/decrypt` (`backend/app/db/crypto.py`). The envelope (`nonce ‖ ciphertext ‖ tag`, URL-safe base64) is MedHub's own format, and AES-256-GCM is a fixed standard, so a conforming library decrypts any earlier ciphertext. Failure mode if not: existing `clinical_entry.description` values raise `InvalidTag`. That is unavailability or loss of PHI already at rest, RISK-011's "old rows fail to decrypt" at its severity 3. The failure is loud, because `decrypt` raises and never returns partial plaintext (TS-008 fault-handling criterion). It is not silent misreading. The 50.0.0–50.0.2 changelog has no AEAD or AES-GCM change: it covers the PKCS#7 fix, FFDH deprecation, X.509/ASN.1 parsing strictness and wheel rebuilds. The bundled OpenSSL moves within the 4.0 line, to 4.0.3. No new hazard. | RISK-011 and RISK-001 at-rest field-encryption control: code unchanged, now running on a changed SOUP item. The AC-9 known-answer test is the §7.4.3 evidence that the control still holds for data already at rest. | New TS-008 TC-008.5 (KAT, ciphertext made under 49.0.0) and TC-008.2 (round trip) under 50.0.2. AC-8 version check. SOUP-011 review (AC-14) |
| anyio 4.14.0 → 4.14.2 (TASK-164) | SOUP-003 (transitive of Starlette 1.3.1); SI-API middleware chain (ADD-005; `SecurityHeadersMiddleware`, `CsrfEnforcementMiddleware` subclass `BaseHTTPMiddleware`, which runs on anyio task groups and memory streams) | Two patch releases. The 4.14.2 changelog lists the PRB-047 fixes (subprocess groups, process-pool stderr, IDNA in `TLSStream`), which MedHub does not use. It also fixes `CapacityLimiter` over-granting tokens on asyncio. Starlette's thread pool uses that limiter, so the limit is now honoured exactly. That is a correction in the safe direction, not a new behaviour. It also fixes unnecessary CPU spin when `CancelScope` delivers a cancellation on asyncio, which `BaseHTTPMiddleware` triggers through `task_group.cancel_scope.cancel()` (a CPU-only fix, in the safe direction). 4.14.1 changes pytest-plugin fixture teardown, `CapacityLimiter.total_tokens` handling of 0 outside an event loop, and two asyncio `Process` fixes (`wait()`, `aclose()`) that MedHub does not reach. A regression in task groups or streams would surface as failed requests or missing headers. It would be visible and caught by tests, not a silent pass. No new hazard. | RISK-005 and RISK-001 (security headers, CSRF enforcement, SR-031): code unchanged, re-verified. | TS-011 header and CSRF tests; full backend suite (AC-18). AC-8 version check. SOUP-003 review (AC-14) |
| urllib3 2.7.0 → 2.8.0 (TASK-164) | SOUP-019 (transitive of botocore 1.43.117); SI-ATTACH object-storage path (ADD-012, SR-013, SR-022 SSE request) | Minor release that fixes the three PRB-047 advisories. Its one behaviour change applies to HTTPS proxies, and none is configured. It deprecates an empty `Retry.allowed_methods`, and botocore uses its own retry handler. urllib3 only carries the request. The `ServerSideEncryption` header is set by botocore and passes through unchanged. A transport regression fails the upload or download loudly (RISK-007). It cannot store an object in plaintext without the request failing. No new hazard. **Pre-existing gap:** no automated test sends a real request to MinIO (PRB-036), so this path is verified by the instantiation test and a manual attachment round trip, not end to end in CI. | RISK-007 and RISK-011 (SSE request, attachment availability): code unchanged, now running on a changed transitive. | TS-007 TC-007.5. Manual attachment upload and download through the proxy on the Compose stack at Checkpoint A (TASK-164). AC-8 version check. SOUP-019 review (AC-14) |
| openapi-fetch removed; ADD-023 and arc42 corrected (TASK-165, TASK-166, TASK-167) | SOUP-033; SI-FE-APICLIENT (ADD-023) | Not imported, so not in the bundle. The emitted bundle is expected to be byte-identical before and after (TASK-165 compares the `dist/` checksums). The record correction removes a misattribution: ADD-023 credited the SR-031.3 client-side CSRF control to a generated, SOUP-backed client, when it is in-house code that must be reviewed as such (PRB-044). No new hazard. | RISK-005: unchanged at runtime; the description of the control's implementation is corrected. RISK-010: `relates_to` SOUP-033 removed. | Frontend lint, typecheck, build and suite (AC-10). `dist/` checksum comparison. `traceability-check` (AC-11, AC-19) |
| Anomaly reviews, RISK-010 and end-to-end verification (TASK-168) | SOUP-003, 011, 019, 021 | The reviews add nothing themselves. Their findings are inputs to this stage (AC-14). | RISK-010 protective control "anomaly and advisory review", re-run at the new versions | TS-013 TC-013.9; gap report (AC-19) |

**RISK-010 (AC-15), revised to 1.4 at this stage.**

- The `relates_to` → SOUP-033 link is removed.
- The path-1 rationale now states that PRB-035 is resolved by TASK-162 (Node 24 LTS, end of life
  2028-04-30). Even while PRB-035 was open, it did not reopen the path, because `npm ci` installs
  only locked versions. TASK-168 confirms the statement once TASK-162 has landed.
- A new entry under "risks introduced by controls" covers the upstream rebuild of a pinned tag
  (observation below).
- **Residual confirmed at 3 × 2 → `alarp`, derived from `risk_matrix`, not re-scored.** The worst
  path still governs. Path 2 (MinIO, SOUP-022/023) is unchanged, because its controls belong to
  CR-002. Path 1 stays at probability 1: this CR is the PLAN-002 counterweight working, with each
  upgrade made by a reviewed commit that changes a lock or a digest, and a dated review at the
  new version.
- The record is `in_review`. **Acceptance of the residual is the human's decision**, through the
  approval of RISK-010 1.4. The ALARP justification is unchanged: the residual is not justified
  for a release until CR-002.

**Observation (2026-10-29): upstream rebuilt a pinned tag.** Docker Hub shows `redis:7.4.11-alpine`
rebuilt on 2026-10-26. The tag now resolves to index digest `sha256:d9436322…3193`, not the
`sha256:892022f9…eab1` that CR-001 pinned. The pinned digest still resolves and is unaffected.
This shows that a release tag alone does not identify an image, and the digest does (SR-028 AC-5).
It also means a base-OS rebuild under the same tag reaches MedHub only through a digest change,
which RISK-010's "pinning delays security patches" already covers. No PRB: nothing is defective.
The observation is recorded in RISK-010 and SOUP-021 (TASK-161).

**Escalations (AC-14).** None at the Risk stage. TASK-161, TASK-163 and TASK-164 add any
hazard-relevant finding here as a RISK, and any MedHub-affecting defect as a PRB. TASK-168 checks
that this list is complete.

- TASK-161 (SOUP-021, review of 2026-10-29): none. No hazard-relevant finding and no MedHub-affecting
  defect, so no RISK raised for SOUP-021. Redis findings carry forward from CR-001 (CVE-2026-92925,
  GHSA-2r7g-8hpc-rpq9); 97 minor Debian base-OS entries have no bookworm fix and are not reachable
  through the Redis protocol. A separate defect, outside this CR, was found while testing:
  [PRB-049](../problem-reports/PRB-049-setup-test-data-script-fails-on-datetime-utc.md)
  (`backend/scripts/setup_test_data.py` fails on `datetime.UTC`; minor, developer tooling).
- TASK-163 (SOUP-011, review of 2026-10-29): none. No anomaly applies to cryptography 50.0.2,
  cffi 2.0.0 or pycparser 3.0, and GHSA-g6cj-pr64-35w5 is fixed at 50.0.0. No OpenSSL advisory
  lists the bundled 4.0.3 as affected. No hazard-relevant finding and no MedHub-affecting defect,
  so no RISK raised for SOUP-011. A separate defect, outside this CR, was found by the QA review of
  TASK-162:
  [PRB-050](../problem-reports/PRB-050-frontend-docker-build-context-copies-host-node-modules.md)
  (`frontend/` has no `.dockerignore`, so a local image build copies the host's `node_modules` and
  `dist`; minor, local build reproducibility, CI unaffected).
- TASK-164 (SOUP-003 and SOUP-019, reviews of 2026-10-29): none. No anomaly applies to Starlette
  1.3.1 with anyio 4.14.2 and idna 3.18, and none to boto3 1.43.117 with botocore, s3transfer,
  jmespath and urllib3 2.8.0. The six PRB-047 advisories for these two packages are fixed at
  anyio 4.14.2 and urllib3 2.8.0. No hazard-relevant finding and no MedHub-affecting defect, so no
  RISK raised for SOUP-003 or SOUP-019. PRB-047 is `resolved` (all three packages).
- TASK-168 (completeness check, 2026-10-30): the list has an entry for each of SOUP-003, SOUP-011,
  SOUP-019 and SOUP-021, and each says "none". No review raised a RISK, and the only PRBs raised
  during the CR (PRB-049, PRB-050) are tooling defects outside the four reviewed items.

### Selected versions (Plan stage, 2026-10-29)

The Software Architect role checked these on 2026-10-29 against published upstream sources. The
human decided the Redis variant (D-1). The digests are the multi-arch index digests that
`registry-1.docker.io` returned (`Docker-Content-Digest` of the index manifest). This
workstation's Docker daemon did not respond, so nothing was read from inside an image. The
developer re-resolves each digest at implementation time. If a digest has changed, the developer
uses the new one and records the change in the task.

| Component | Selected | Support / release evidence (source, checked 2026-10-29) |
|---|---|---|
| Redis server (SOUP-021) | `redis:7.4.12-bookworm@sha256:b6b6e3dc0c0952737748e55d5d885272840c7e42ba41ab1d5489f693419882f5` | Redis 7.4.12, released 2026-10-26 (github.com/redis/redis/releases/tag/7.4.12, "SECURITY" urgency). Redis 7.4 end of life 2029-12-01 (endoflife.date/redis). Base image `FROM debian:bookworm-slim` (redis/docker-library-redis `release/7.4/debian/Dockerfile`). Debian 12 "bookworm": regular security support ended 2026-07-11, Debian LTS until **2028-06-30** (endoflife.date/debian; wiki.debian.org/LTS), 20 months after the change (Q-2, D-1) |
| Node build stage (tooling, A-3) | `node:24.22.2-trixie-slim@sha256:54f84b4cf8432b21aaffd5d3ce8d41e12cea0d10d33c09d2f3c9879d49d6b446` | Node 24.22.2 "Krypton", released 2026-10-27 (nodejs.org/dist/index.json). Node 24: Active LTS from 2025-10-28, Maintenance LTS from 2026-10-20, end of life **2028-04-30** (github.com/nodejs/Release `schedule.json`), 18 months after the change (Q-2). The explicit `-trixie-slim` tag is used because the bare `-slim` alias resolves to bookworm for Node 24. Every locked frontend toolchain package declares a `node` engine range that includes 24 (`frontend/package-lock.json`) |
| CI `node-version` | `"24"` in `frontend-quality`, `frontend-tests`, and the new `setup-node` step of `openapi-lint` (Q-3) | Same major as the build stage (AC-4). The patch is not pinned in CI (PRB-034, out of scope) |
| anyio (SOUP-003 transitive) | **4.14.2**, pinned explicitly (`uv lock --upgrade-package anyio==4.14.2`) | PyPI (pypi.org/pypi/anyio/json): 4.14.2 uploaded 2026-07-12, the first release with the PRB-047 fixes. The newest release, 4.15.1 (2026-09-05), is not chosen: 4.14.2 is the smallest move that fixes the advisories (D-3) |
| urllib3 (SOUP-019 transitive) | **2.8.0** | PyPI: 2.8.0 uploaded 2026-09-15. It is the only release with the PRB-047 fixes and also the newest |
| cryptography (SOUP-011) | **50.0.2** | PyPI: 50.0.2 uploaded 2026-09-30, the newest 50.0 patch (AC-7). 50.0.0 (2026-07-31) fixes GHSA-g6cj-pr64-35w5 |

Redis alternatives considered at the Plan stage (evidence for D-1, checked 2026-10-29):

- **Every Redis 7.4 Alpine image is on Alpine 3.21.**
  - Docker Hub lists `7.4.2-alpine3.21` through `7.4.12-alpine3.21` (Docker Hub tags API,
    `library/redis`, filter `7.4`).
  - `docker-library/official-images` `library/redis` maps `7.4.12-alpine`, `7.4-alpine` and
    `7-alpine` to `7.4.12-alpine3.21`.
  - The upstream `release/7.4/alpine/Dockerfile` starts `FROM alpine:3.21`.
- **No newer Alpine branch is available for 7.4.** Alpine 3.21 ends support on 2026-11-01. Alpine
  3.22 ends on 2027-05-01, which fails Q-2. No Redis 7.4 image exists on Alpine 3.23 or 3.24
  (endoflife.date/alpine-linux).
- **The 7.4.12 variants are `-alpine3.21` and `-bookworm` only.** There is no trixie variant
  (the orchestrator confirmed this on Docker Hub).
- **Rejected:**
  - Redis 8.x on Alpine 3.23, which is out of scope (licence and behaviour change).
  - A MedHub-built 7.4 image on a newer Alpine, which would make MedHub own the image build.
  - 7.4.12 on Alpine 3.21 with Q-2 waived, which would leave PRB-045 unresolved.

## Acceptance criteria

Redis image (PRB-045)

- **AC-1:** The `redis` service `image:` in `infra/docker-compose.yml` and the `redis` service
  container `image:` of the `backend-tests` job in `.github/workflows/ci.yml` are the identical
  reference, of the form `redis:7.4.<patch>-bookworm@sha256:<64 hex>`. The tag names a full
  Redis **7.4** patch release and the official Debian 12 variant (D-1). No reference uses
  `7-alpine`, `7.4-alpine`, `7`, `7.4`, `bookworm` or `latest`, or any other tag without a patch
  component. *(Amended 2026-10-29, human decision D-1: was "an Alpine variant".)*
- **AC-2:** The base OS release of that image is in upstream support on the date of the change and
  stays in support for at least 12 months after it (Q-2). Upstream support means Debian security
  support or Debian LTS. Status and dates are judged against https://www.debian.org/security/,
  https://wiki.debian.org/LTS and endoflife.date/debian, and recorded with the date of the check.
  The evidence is `/etc/os-release` (`VERSION_ID="12"`, `VERSION_CODENAME=bookworm`), read from
  the pinned image without starting Redis. *(Amended 2026-10-29, human decision D-1: was "an
  Alpine branch … `/etc/alpine-release`".)*

Node build runtime (PRB-035)

- **AC-3:** The build stage of `frontend/Dockerfile` has the form
  `FROM node:<major>.<minor>.<patch>-<variant>@sha256:<64 hex> AS build`. `<major>` is a Node.js
  release line in Active LTS or Maintenance LTS on the date of the change, and its published
  end-of-life date is at least 12 months after that date (Q-2). Status and dates are judged
  against the Node.js release schedule (https://github.com/nodejs/Release). The runtime stage
  (`nginx:1.31.8-alpine@sha256:e2d9…`) does not change.
- **AC-4:** The `frontend-quality` and `frontend-tests` jobs in `.github/workflows/ci.yml` set
  `node-version` to the same major as AC-3, and no step name in the file says "Node.js 20".
  If Q-3 is accepted, `openapi-lint` installs that same major with `actions/setup-node` before
  its first `npx` or `npm` step. No job in the file installs Node 20.
- **AC-5:** The CI `build` job builds the frontend image with the AC-3 stage, and `npm ci` and
  `npm run build` succeed in it. The Node change alone leaves `frontend/package-lock.json`
  unchanged: same `lockfileVersion`, same resolved versions. The only lock change in this CR is
  the one AC-10 makes.
- **AC-6:** The verification-environment line of TS-001..TS-013 names the AC-3 Node line instead
  of "Node 20". TP-001, TR-001 and TR-002 are not changed.

Python transitives (PRB-047)

- **AC-7:** `backend/uv.lock` resolves anyio to 4.14.2 or later, urllib3 to 2.8.0 or later, and
  cryptography to a 50.0.x release (the newest 50.0 patch on the date of the change), and
  `uv lock --check` succeeds. In the lock diff, no other package changes version, except packages
  that the new versions require. Each such package is named, with its old and new versions, in
  the task record and is covered by the review under AC-14.
- **AC-8:** In the built backend image (installed with `uv sync --frozen --no-dev`),
  `importlib.metadata.version()` reports the AC-7 versions of `anyio`, `urllib3` and
  `cryptography`.
- **AC-9:** An automated backend test, run in CI on every pull request, decrypts a fixed
  ciphertext with `backend/app/db/crypto.py`. The ciphertext was produced under cryptography
  49.0.0 from a fixed test key, nonce and plaintext, all committed as test data, and the test
  gets back the original plaintext. The test passes under the AC-7 version. It is recorded as a
  test case in TS-008, which verifies SR-022 (Q-4).

openapi-fetch (PRB-044)

- **AC-10:** `openapi-fetch` appears in no section of `frontend/package.json`. In
  `frontend/package-lock.json`, the `node_modules/openapi-fetch` and
  `node_modules/openapi-typescript-helpers` entries and the root-package dependency on
  `openapi-fetch` are removed, and nothing else changes. `npm ci`, `npm run lint`,
  `npm run typecheck` and `npm run build` succeed.
- **AC-11:** SOUP-033 has `status: obsolete`, a bumped `version` and a change-log entry citing
  PRB-044 and CR-003. No record that is not `obsolete` keeps a `relates_to` link to SOUP-033:
  the links from ADD-023 and RISK-010 are removed.
- **AC-12:** ADD-023's Responsibility section and its `U-FEAPI-Client` unit describe what the
  code does:
  - the hand-written `ApiClient` (`frontend/src/api/client.ts`) over the browser `fetch`, with
    CSRF and RFC 7807 handling;
  - request and response types generated by the dev tool `openapi-typescript` into
    `frontend/src/api/generated/`.

  No statement says that the client or its methods are generated, in ADD-023 or in
  `docs/design/03-context-and-scope.md`, `docs/design/05-building-blocks.md` (table row and
  SI-FE-APICLIENT unit), `docs/design/12-interfaces.md` (SI-FE-APICLIENT row) or
  `docs/specifications/diagram-building-blocks.puml`. ADD-004 stays `obsolete`, with a bumped
  `version` and a correction note in its obsolete banner that names the wrong `openapi-fetch`
  row and PRB-044.

SOUP records (all four PRBs)

- **AC-13:** The `soup_version` of SOUP-021 equals the Redis release in the AC-1 tag. The
  `soup_version` of SOUP-011 equals the locked cryptography version. SOUP-003 and SOUP-019 keep
  their `soup_version` (Starlette 1.3.1, boto3 1.43.117) unless the lock changes those packages
  too. Their bodies record the new anyio and urllib3 versions, and any other transitive version
  that AC-7 changes. SOUP-021's body lists the full image reference with its digest, both files
  that use it, and the base-OS branch, its version and its end-of-support date. No body states a
  replaced version as current. Each record has a change-log entry citing its PRB and CR-003.
- **AC-14:** SOUP-003, SOUP-011, SOUP-019 and SOUP-021 each meet three conditions:
  - Their `anomaly_review` is the date of a new review, on or after 2026-10-29, done at the AC-13
    versions.
  - Their "Anomaly list review" section cites each source checked, by name and URL, for those
    exact versions. For SOUP-021 that includes every source package of the base OS at its
    installed version.
  - The section lists every applicable anomaly with a hazard-relevance judgement, or states
    "none found". It shows each PRB-047 advisory as fixed at the new version and the PRB-045
    end-of-support finding as cleared.

  Hazard-relevant findings become RISK records, and findings that affect MedHub become PRBs.
  This CR's body lists each escalation, or states that there were none.

Risk

- **AC-15:** The Risk-stage change analysis in this CR covers every change in Scope and every
  RISK record linked to SOUP-003, 011, 019, 021 or 033, and states whether the change introduces
  a hazard or raises the software safety class. RISK-010 is revised: its `relates_to` → SOUP-033
  link is removed, its path-1 rationale no longer cites PRB-035 as open, and its residual is
  confirmed, or re-scored against `risk_matrix` with a rationale.

Verification and records

- **AC-16:** On the branch head, `python3 infra/check_image_pins.py` exits 0 and
  `uv lock --check` (in `backend/`) succeeds.
- **AC-17:** The pinned stack works. `docker compose -f infra/docker-compose.yml build` succeeds,
  the stack starts, and `infra/smoke-test.sh` passes 17/17. The running `redis` container reports
  the AC-1 Redis version.
- **AC-18:** Every job in `.github/workflows/ci.yml` passes on the branch head. Locally, the
  backend suite (`pytest`, coverage at or above the CI threshold of 85 %) and the frontend suite
  (Vitest) pass.
- **AC-19:** PRB-045, PRB-035, PRB-047 and PRB-044 are `resolved`. Each has a `## Resolution`
  that names the changed files and a reproducible verification, and each has an incoming
  `resolves` link from this CR. Every design record this CR creates or changes is `in_review`,
  apart from SOUP-033 and ADD-004, which are `obsolete`. `traceability-check` over the whole
  project reports 0 errors and no `soup_anomaly_review_stale` warning for any non-obsolete SOUP
  record.

## Verification approach

IEC 62304 §8.2.1 (change approval), §8.2.3 (verification of changes) and §7.4.3 (verification of
risk-control measures after a change).

- **Static checks (AC-1, AC-3, AC-4, AC-7, AC-10, AC-16):** the changed files are inspected
  against the criteria. The pin check and `uv lock --check` run in CI. The two lock diffs are
  reviewed line by line against AC-5, AC-7 and AC-10.
- **Supported-version evidence (AC-2, AC-3):** the upstream support pages and the dates read from
  them are recorded, with the date of the check, in this CR ("Selected versions"), in the task
  records (Node in TASK-162, Debian in TASK-161) and in SOUP-021 (Debian).
  `/etc/os-release` is read from the pinned Redis image (AC-2 as amended by D-1).
- **Production dependency set (AC-8):** a check against the built backend image. *Plan-stage
  decision (D-4):* it runs once and is not added to CI. TASK-164 records it, and the next TR
  copies it.
- **Ciphertext compatibility (AC-9):** the known-answer test in the backend suite, added to
  TS-008.
- **Integration (AC-17):** a Compose build and start of the pinned stack, then
  `infra/smoke-test.sh`, run on the branch. That covers the session store and the broker on the
  new Redis image.
- **Regression (AC-5, AC-18):** the full CI pipeline on the branch head, including the frontend
  image build, the TS-001 session tests (Redis), the TS-008 encryption tests (cryptography), the
  TS-011 header and CSRF tests (Starlette and anyio) and the TS-007 attachment tests (urllib3
  under boto3).
- **Anomaly review (AC-13, AC-14):** the human reviews each updated SOUP record's review section
  and its cited sources when approving the records.
- **Records (AC-6, AC-11, AC-12, AC-15, AC-19):** `traceability-check`, and human approval of the
  SOUP records, RISK-010, ADD-023, TS-008 and TS-001..013.

Results go into the next test report (TR) for the release.

## Assumptions

- **A-1:** One CR is enough despite PRB-045's deadline. No release exists, and none is made
  before CR-002, so the days on an unsupported base OS affect only development, CI and
  pre-release environments. If the human wants `main` on a supported base OS before 2026-11-01,
  PRB-045 can be split into its own CR. The criteria are grouped by PRB, so the split is
  mechanical (Q-1).
- **A-2:** "Supported" means upstream support on the date of the change, plus the 12-month
  horizon of AC-2 and AC-3 (Q-2). The architect picks the exact versions within these
  constraints and records the support dates.
- **A-3:** The Node build image stays tooling, not SOUP, as in CR-001 A-3: it builds the bundle
  but is not shipped. So it gets no SOUP record and no anomaly-list review. Its support status is
  still a criterion (AC-3), because the PRB-035 defect is exactly that status.
- **A-4:** For a transitive dependency, `soup_version` stays the version of the parent component
  that the record is named after. The transitive's version is recorded in the body, as CR-001
  and TASK-154 did for anyio and urllib3.
- **A-5:** Redis stays on the 7.4 line. A Redis 7.4 patch built on another base OS (Debian 12
  instead of Alpine 3.21, D-1) changes neither the server's behaviour nor the AOF format.
  Both images run `redis` as uid 999, and the entrypoint chowns `/data`. So an existing
  `redis_data` volume is expected to load. TASK-161 confirms this on the reference workstation
  (existing-volume check), and AC-17 confirms the stack. *(Amended 2026-10-29: was "a newer
  Alpine branch".)*
- **A-6:** `cryptography` keeps its `>=42.0.0` floor in `backend/pyproject.toml`. The lock is the
  pin (SR-028 AC-5), and a floor change is made only if AC-7 needs it (Boundaries).
- **A-7:** This CR's status is `open` at handoff. The change-request status set has no
  `in_review`, so the human's approval of the Specify gate is recorded as a decision in this
  record, as CR-001 did.

## Open questions

Each question carries the recommended answer. The criteria above already assume it. **All five
were resolved by the human at the Specify gate on 2026-10-29**. Each answer is recorded under its
question, and the Plan-stage decisions are under "Decisions".

- **Q-1 (deadline):** Keep one CR, with PRB-045 as its first task, or split PRB-045 into its own
  CR and pull request so that `main` changes before 2026-11-01? *Recommended: one CR* (A-1).
  **Resolved (human, 2026-10-29): one CR, with the PRB-045 fix as the first task (TASK-161).**
  Re-confirmed at the Plan stage after D-1. PRB-045 stays in this CR.
- **Q-2 (support horizon):** Must the new Alpine branch and Node line have at least 12 months of
  upstream support left on the date of the change? *Recommended: yes.* Per the published
  schedules, that excludes Node 22 (end of life 2027-04-30) and Alpine 3.22 (end of support
  2027-05-01), which would otherwise bring the same PRB back within six months. The architect
  confirms the dates. Without this rule the minimum is "in support on the date of the change".
  **Resolved (human, 2026-10-29): yes, at least 12 months.** Confirmed dates are in "Selected
  versions". No Redis 7.4 image exists on an Alpine branch that meets this rule, so the human
  accepted Debian LTS as upstream support for the Redis base OS (D-1).
- **Q-3 (`openapi-lint` job):** Should `openapi-lint` also get `actions/setup-node` with the same
  Node line? Today it runs `npx` and `npm ci` on whatever Node the runner image provides
  (`.github/workflows/ci.yml:193`, `:199`). *Recommended: yes, in this CR.* It is one step, and
  without it a frontend job still runs on a Node the repository does not choose.
  **Resolved (human, 2026-10-29): yes.** `openapi-lint` gets `actions/setup-node` with
  `node-version: "24"` (TASK-162).
- **Q-4 (known-answer test, AC-9):** Should a new test check that ciphertexts written under
  cryptography 49.0.0 still decrypt? No current test does: they all round-trip under the
  installed version. *Recommended: yes.* The test is small, and it is the only direct evidence
  that PHI already at rest stays readable after the upgrade (§7.4.3).
  **Resolved (human, 2026-10-29): yes, AC-9 stays in scope** (TASK-163, TS-008 TC-008.5).
- **Q-5 (root cause of PRB-045 and PRB-035):** Should PLAN-002 gain an end-of-support or
  obsolescence criterion (§6.1 f) in this CR? An example: "at each review, record each SOUP
  item's and build image's upstream end-of-support date, and raise a PRB once it is less than six
  months away". *Recommended: no, raise it as its own plan revision.* That way this CR stays a
  component change, and the plan change gets its own review.
  **Resolved (human, 2026-10-29): not in this CR.** The PLAN-002 end-of-support criterion is a
  separate plan revision, which the orchestrator raises.

## Decisions

Recorded at the Plan stage, 2026-10-29. D-1, D-2, D-3 and D-5 were made by the human in chat. D-4
and D-6 are Plan-stage readings by the Software Architect role, open to the human's review at the
plan gate.

- **D-1 (Redis variant; human):** `redis:7.4.12-bookworm`, the official image on Debian 12.
  - Evidence: upstream builds Redis 7.4 on Alpine 3.21 only. Alpine 3.22 ends support on
    2027-05-01, which fails Q-2. No 7.4 image exists on Alpine 3.23 or 3.24, and 7.4.12 has no
    trixie variant. See "Selected versions".
  - The human accepts Debian LTS (until 2028-06-30, endoflife.date) as "upstream support" for Q-2.
  - AC-1, AC-2, scope item 1 and A-5 are amended to match.
  - The musl → glibc and image-size change is analyzed in the Risk-stage change analysis.
- **D-2 (Node; human):** `node:24.22.2-trixie-slim` for the build stage. The tag says
  `-trixie-slim` explicitly, because the bare `-slim` alias resolves to bookworm for Node 24. CI
  uses `node-version: "24"` in `frontend-quality`, `frontend-tests` and `openapi-lint`.
- **D-3 (Python versions; human):**
  - anyio **4.14.2**, pinned explicitly (`uv lock --upgrade-package anyio==4.14.2`), so that the
    resolver does not pick 4.15.1;
  - urllib3 **2.8.0**;
  - cryptography **50.0.2**.
- **D-4 (AC-8 check, run once; architect):** the `importlib.metadata.version()` check of AC-8 runs
  once against the built image. TASK-164 records it and the next TR copies it. It is not added
  to the CI "Check production dependency set" step.
  - The image installs only from the frozen lock (`uv sync --frozen --no-dev`), and
    `backend-quality` runs `uv lock --check`. So the image cannot differ from the lock, and a CI
    assertion would only repeat those two checks.
  - It would also hard-code versions that every later upgrade would have to edit.
  - The CI step keeps its present role: an import and absence check, no versions.
- **D-5 (RISK-011 body; human):** the "Software items involved" line of RISK-011, which names
  cryptography 49.0.0, is corrected in TASK-163. It will name the SOUP record instead of a
  version, so it does not go stale at the next upgrade. RISK-011's scores are not changed.
- **D-6 (AC-11 and this CR's own link; architect):** AC-11 says no record that is not `obsolete`
  keeps a `relates_to` link to SOUP-033. This CR is such a record, so TASK-165 removes this CR's
  `relates_to` SOUP-033 link when it sets SOUP-033 `obsolete`. The body still names SOUP-033, and
  so does TASK-165's link. This follows CR-001, which did not link SOUP-018.

## Implementation plan

The plan is the TASK records below. Under the overlay there is no `docs/plans/<feature>.md`.

- All tasks are on `bug/soup-upgrades`, with one commit per QA-approved task, carrying its records.
- A record that is `approved` and is changed by more than one task gets its version bumped and its
  approval record cleared once in this CR, by the first task that changes it. Later tasks keep
  that version and add to its history entry, as CR-001 did.

| Order | Task | CR-003 AC | Depends on | Size | Docker host / network |
|---|---|---|---|---|---|
| 1 | [TASK-161](../design-outputs/tasks/TASK-161-move-redis-to-7-4-12-on-debian-12.md) Move Redis to 7.4.12 on Debian 12, pinned by tag and digest | AC-1, AC-2, AC-13 (SOUP-021), AC-14 (SOUP-021), AC-17 (part), AC-19 (PRB-045) | none | M | Docker host (image inspect, existing-volume check, Compose run). Network (registry, OSV, Debian tracker, vendor advisories) |
| 2 | [TASK-162](../design-outputs/tasks/TASK-162-build-frontend-and-ci-on-node-24-lts.md) Build the frontend and run CI on Node 24 LTS | AC-3, AC-4, AC-5, AC-6, AC-19 (PRB-035) | none. Commit after TASK-161 (both edit `.github/workflows/ci.yml`, different jobs) | M (2 code files, 13 one-line record edits) | Docker host (frontend image build; or the CI `build` job). Network (registry, npm) |
| 3 | [TASK-163](../design-outputs/tasks/TASK-163-upgrade-cryptography-with-known-answer-test.md) Upgrade cryptography to 50.0.2 behind a known-answer decryption test | AC-7 (cryptography), AC-8 (part), AC-9, AC-13 (SOUP-011), AC-14 (SOUP-011) | none. Must precede TASK-164 (same lock file) | M | Network (PyPI, advisories). Docker only for the *real DB* tests of the full suite |
| 4 | [TASK-164](../design-outputs/tasks/TASK-164-upgrade-anyio-and-urllib3.md) Upgrade anyio to 4.14.2 and urllib3 to 2.8.0 | AC-7, AC-8, AC-13 (SOUP-003, SOUP-019), AC-14 (SOUP-003, SOUP-019), AC-19 (PRB-047) | TASK-163 | M | Docker host (AC-8 image check, attachment round trip). Network |
| — | **Checkpoint A**, after tasks 1–4 | AC-16, AC-17, AC-18 (interim) | — | — | Docker host |
| 5 | [TASK-165](../design-outputs/tasks/TASK-165-remove-unused-openapi-fetch.md) Remove the unused openapi-fetch dependency | AC-10, AC-11 (SOUP-033, this CR's link) | TASK-162 (keeps the AC-5 and AC-10 lock diffs apart) | S | Network (npm) |
| 6 | [TASK-166](../design-outputs/tasks/TASK-166-correct-add-023-api-client-description.md) Correct the API-client design record (ADD-023, ADD-004 note) | AC-11 (ADD-023 link), AC-12 (records) | TASK-165 | S | none |
| 7 | [TASK-167](../design-outputs/tasks/TASK-167-correct-api-client-description-in-arc42.md) Correct the API-client description in arc42 and the building-block diagram | AC-12 (arc42, diagram), AC-19 (PRB-044) | TASK-166 | S | none |
| 8 | [TASK-168](../design-outputs/tasks/TASK-168-verify-cr-003-end-to-end.md) Confirm RISK-010 and the anomaly reviews, and verify CR-003 end to end | AC-11 (check), AC-14 (escalations), AC-15, AC-16, AC-17, AC-18, AC-19 | all above | S | Docker host. Network (CI on the branch head) |

**Parallel work.** Tasks 1, 2 and 3 share no file except `.github/workflows/ci.yml`, which tasks 1
and 2 edit in different jobs, so they can be worked in parallel and committed in order. Tasks 6
and 7 are documentation only, and the Document Writer may do task 7 (the arc42 split).

**Checkpoint A (after TASK-161..164).**

- All CI jobs are green on the branch head.
- `python3 infra/check_image_pins.py` exits 0, and `uv lock --check` passes.
- The backend suite passes with coverage ≥ 85 %, and the frontend suite passes.
- The pinned stack builds and starts. `infra/smoke-test.sh` passes 17/17, `redis-cli INFO server`
  reports 7.4.12, and an attachment uploads and downloads through the proxy.
- Every runtime change of this CR is then in place. Tasks 5–7 change no runtime component.

**Checkpoint B** is TASK-168: the end-to-end run over the whole CR.

### AC coverage

| AC | Task(s) |
|---|---|
| AC-1 | TASK-161 |
| AC-2 | TASK-161 |
| AC-3 | TASK-162 |
| AC-4 | TASK-162 |
| AC-5 | TASK-162 (confirmed by TASK-168: the CI `build` job) |
| AC-6 | TASK-162 |
| AC-7 | TASK-163 (cryptography), TASK-164 (anyio, urllib3, full lock diff) |
| AC-8 | TASK-163 (cryptography), TASK-164 (all three, on the built image; D-4) |
| AC-9 | TASK-163 |
| AC-10 | TASK-165 |
| AC-11 | TASK-165 (SOUP-033 obsolete, this CR's link), TASK-166 (ADD-023 link), RISK-010 link removed at the Risk stage; TASK-168 checks |
| AC-12 | TASK-166 (ADD-023, ADD-004), TASK-167 (arc42 sections, diagram) |
| AC-13 | TASK-161 (SOUP-021), TASK-163 (SOUP-011), TASK-164 (SOUP-003, SOUP-019) |
| AC-14 | TASK-161, TASK-163, TASK-164 (reviews); TASK-168 (escalation list, completeness) |
| AC-15 | Risk stage (this CR, RISK-010 1.4); TASK-168 confirms after TASK-162 |
| AC-16 | every task; TASK-168 on the branch head |
| AC-17 | TASK-161 (Redis version, existing volume), Checkpoint A, TASK-168 |
| AC-18 | every task (its suites); TASK-168 (every CI job on the branch head) |
| AC-19 | TASK-161 (PRB-045), TASK-162 (PRB-035), TASK-164 (PRB-047), TASK-167 (PRB-044), TASK-168 (statuses, `traceability-check`) |

Every AC-1..AC-19 maps to at least one task.

### Plan risks

| Risk | Impact | Mitigation |
|---|---|---|
| Upstream rebuilds a selected tag before implementation (as it did for `7.4.11-alpine`), so the digest changes | Pinned digest differs from the one recorded here | The developer re-resolves each digest and records any change in the task and the SOUP change log (TASK-161, TASK-162) |
| `uv lock --upgrade-package` pulls in more than the named package | Out-of-scope lock change (AC-7 Boundaries) | The task pins with `name==version`, inspects the lock diff line by line, and lists any required extra package with old and new versions. Anything else is reverted and constrained (TASK-163, TASK-164) |
| The KAT fixture is generated after the lock changes | AC-9 would prove nothing about 49.0.0 data | TASK-163 writes and commits the fixture under the current lock **before** touching `uv.lock`, and records `cryptography.__version__` from the generating run |
| Existing `redis_data` volume fails to load under the Debian image | Sessions and queued tasks lost on the reference workstation | The data is not PHI. TASK-161's existing-volume check finds it first. Fallback: `docker compose down -v` for `redis_data` only, after the human agrees |
| No Docker daemon on the workstation (seen 2026-10-29) | AC-2, AC-8, AC-17 and the attachment check cannot be run locally | Run on a Docker host (the reference workstation with Docker Desktop running). CI covers the image builds and the service container, but not AC-17 |
| Debian LTS does not cover every package | A base-OS package of the Redis image may get no fixes | The SOUP-021 review checks `debian-security-support`'s list of packages with limited support against the installed packages. A covered gap becomes a finding (AC-14) |

## Version history

- 1.0 (2026-10-29) — Created at the Specify stage of issue sancharly/medhub#32. Resolves
  PRB-045, PRB-035, PRB-047 and PRB-044. Preliminary `risk_impact`: `affects_controls`.
  CR-002 is reserved for the MinIO controls (CR-001, human decision 2026-10-22), so this CR
  takes the next free ID, CR-003.
- 1.1 (2026-10-29) — Risk and Plan stages (Software Architect role).
  - Q-1..Q-5 resolved, recording the human's Specify-gate answers.
  - Decisions D-1..D-6 added. D-1 (Redis on the Debian 12 variant), D-2, D-3 and D-5 are the
    human's, made at the Plan stage after the architect reported that no Redis 7.4 image exists on
    an Alpine branch that meets Q-2.
  - AC-1, AC-2, scope item 1, A-5 and the verification approach amended for D-1. Scope item 3
    gains the RISK-011 body correction (D-5).
  - "Change analysis (Risk stage, 2026-10-29)" added: `affects_controls` confirmed, no new
    hazard, class B unchanged. "Selected versions" added, with the evidence. The observation of
    the upstream rebuild of `redis:7.4.11-alpine` recorded.
  - RISK-010 revised to 1.4 (`in_review`).
  - Implementation plan TASK-161..168 added, with checkpoints, the AC coverage table and the plan
    risks. `relates_to` links to the tasks and to RISK-011 added.
  - Status stays `open`.
- 1.2 (2026-10-30) — TASK-168 (Checkpoint B). Escalations list confirmed complete. Status stays `open`.
