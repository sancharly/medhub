---
id: "PRB-042"
type: problem-report
title: "MinIO community edition is unmaintained and its images can no longer be obtained"
status: resolved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-30"
criticality: major
links: []
tags: ["soup", "configuration-management", "maintenance", "hazard:availability", "hazard:security"]
---

# PRB-042 — MinIO community edition is unmaintained and its images can no longer be obtained

## Observed

The object store [SOUP-022](../soup/SOUP-022-minio.md) (`minio/minio:RELEASE.2025-09-07T16-13-09Z`)
and the bucket initialiser [SOUP-023](../soup/SOUP-023-minio-client.md)
(`minio/mc:RELEASE.2025-08-13T08-35-41Z`) are no longer distributed or maintained by their
manufacturer. Evidence from MinIO's own notices, checked 2026-10-22 (CR-001 D-4):

- **2025-10-15**, `minio/minio` README commit `9e49d5e7a6`: the community edition is distributed as
  source code only; no more pre-compiled binaries, and the legacy ones receive no updates.
- **2025-10-16**: `RELEASE.2025-10-15T17-29-55Z` is published with no assets, and its notes tell
  container users to build their own image. The pinned server release is therefore the last
  community release with binaries and images. The pinned `mc` release is `mc`'s last release.
- **2025-12-03**, README commit `27742d4694`: maintenance mode. Security fixes only "case-by-case".
- **2026-02-12**, README commit `7aac2a2c5b`: the repository is declared no longer maintained, and
  the alternatives offered are the proprietary AIStor editions.
- **April 2026**: `minio/minio` is archived (last push 2026-04-24). `minio/mc` is archived too (last
  push 2025-11-20).
- **2026-10-22**: `dl.min.io` returns HTTP 410 for community downloads. The notice says the
  community server, client and KES receive no support, no security updates and no advisories.
- Every MinIO advisory of 2026 gives its fix in MinIO AIStor only.
- **2026-10-22**: Docker Hub returns 404 for `minio/minio` and `minio/mc`, and quay.io returns 401.
  `docker compose pull` cannot obtain either image.
- The archived GitHub releases still list their binaries (`.sha256sum`, `.asc` and `.minisig`
  files included). An HTTP HEAD request for the linux-amd64 binaries of both pinned releases
  returned 200 on 2026-10-22.

The workstation cache holds both images, arm64 only, and CR-001 pinned their local RepoDigests
(TASK-155).

## Impact

- **§5.8.5 (build reproducibility):** a fresh or amd64 host cannot build or start the stack from
  `infra/docker-compose.yml`. `backend` `depends_on` `createbuckets`, which needs the `mc` image.
  CR-001 AC-5 is reproducible only on a host holding the cache.
- **§6.1 f (SOUP maintenance):** the PLAN-002 review cadence can detect new anomalies in this
  item but can never lead to a patch. Four unfixed vulnerabilities are already hazard-relevant in
  MedHub's configuration (PRB-043). The image's RHEL 9.6 UBI base OS has had no update since
  2025-09-07 and will not be rebuilt.
- **Risk records:**
  - [RISK-012](../risks/RISK-012-object-store-compromised-or-unpatchable.md) (new) records the
    hazard.
  - RISK-007: deployment on a new host fails.
  - RISK-010: its "pinning delays patches" counterweight does not hold for this item. The input
    goes to TASK-159.
  - RISK-011 and RISK-001: the SSE server receives no security fixes.

## Investigation

Root cause: the manufacturer withdrew the community edition. The evidence is in the Observed list:
source-only from 2025-10-15, maintenance mode 2025-12-03, no longer maintained 2026-02-12, archived
April 2026, community downloads answering HTTP 410 and the Docker Hub and quay.io images gone on
2026-10-22.

MedHub's side of the problem: `infra/docker-compose.yml:96` and `:114` pin the server and `mc` by
tag and digest (CR-001), but the pinned references name images that no registry serves, and the
`backend` service depends on `createbuckets`, which needs the `mc` image. A host without the cached
arm64 images cannot start the stack. Which maintained store or interim build resolves it is an
architecture decision (ADR of CR-002); this report does not decide it.

## Safety evaluation

The availability effect shows at deployment: the stack fails to start before any clinical use, so
on its own it creates no hazardous situation. The security effect is that every future anomaly
in the SSE server stays unfixed. Combined with the configuration in PRB-043, that already
contributes to RISK-012 (severity 4 × probability 2, alarp), and PRB-043 carries the immediate
exposure. This report is `major` rather than `critical`. It blocks reproducible deployment and
any lasting security maintenance of a component that carries a risk control (SR-022 SSE, RISK-011).
It does not by itself corrupt data, misattribute data or mislead a clinical decision.

Released versions (§9.3): no `release` record exists (`docs/releases/` is absent), so no released
version in use is affected and no notification is needed.

## Proposed resolution

- **CR-002** (human decision, 2026-10-22), with an ADR choosing a maintained S3-compatible object
  store. Options include the AIStor Free licence or another maintained server. The ADR must cover
  SSE-S3 support, the licence, image availability and digest pinning, and the migration of
  existing objects and key material (RISK-011).
- **Interim, also in CR-002:** build the object-store and client images from the archived release
  binaries, verifying their published SHA-256 checksums and signatures. Pin the result by digest
  so a fresh or amd64 host can deploy. Record the change in SOUP-022 and SOUP-023.
- Update SOUP-022 and SOUP-023 (or make them `obsolete` when the component is replaced), PLAN-002
  monitoring if the replacement changes it, and RISK-012.
- Not changed by CR-001 (D-4, A-4).

## Resolution

Resolved by the TASK-176 commit on `bug/minio-object-store` (subject "FIX: Replace the MinIO
server with SeaweedFS pinned by digest (TASK-176)"), under CR-002 and
[ADR-0015](../design/adr/0015-object-store-component-after-minio.md) (Accepted, CR-002 D-6: the
human chose SeaweedFS). The unmaintained component leaves the deployment:

- `infra/docker-compose.yml`: the `minio` service is replaced by `object-store`, image
  `chrislusf/seaweedfs:4.51@sha256:f7a49e3f3972ebed5be2ed4befa4a0c68eb7bdddba6e692d42729ceb545134b8`
  (OCI index digest, linux/amd64 and linux/arm64; Apache-2.0; SOUP-036). The `minio/minio` and
  `minio/mc` references are gone (`mc` since TASK-175). The command is `weed server` with master,
  volume server and filer on loopback and no admin UI, WebDAV or SFTP (SR-040 AC 1).
- [SOUP-022](../soup/SOUP-022-minio.md) is `obsolete`; [SOUP-036](../soup/SOUP-036-seaweedfs.md)
  is linked from [ADD-025](../design-outputs/architecture/ADD-025-object-store-deployment.md).
- Existing data in `minio_data` is not read by the new server; the volume stays declared and
  untouched. Moving it is TASK-178; network restriction is TASK-177; CI evidence is TASK-179.

Verification (TASK-176, 2026-10-30; commands and results in the TASK "Verification results" and
TS-013 TC-013.10, TS-014 TC-014.1 and TC-014.5):

```sh
python3 infra/check_image_pins.py                      # exit 0
python3 -m unittest discover -s infra/tests -v         # 24 tests OK
grep -n "9001\|console\|minio/minio\|minio/mc" infra/docker-compose.yml   # no output
```

Fresh-host evidence (2026-10-30, arm64 Docker Desktop host). An amd64 `docker:dind` does not start
on this host (iptables under emulation), so the daemon under test was an **arm64-native**
`docker:dind` with an empty image store, and only its client was set to amd64 with
`DOCKER_DEFAULT_PLATFORM=linux/amd64`; every image in the result runs as `linux amd64` under
emulation. Exact commands (also in TASK-176 "Verification"):

```sh
docker run -d --name cr002-dind --privileged -e DOCKER_TLS_CERTDIR= \
  docker@sha256:cb160a57fcb936668f8ab8e4a9d73c66b7975226aa87e466233734edbcd83ccc
  # arm64 entry of the docker:dind index sha256:9e79b879b177fbd72c34376a3dd3d91747da5db49e1f560f76aea59561471977
docker exec cr002-dind docker info --format 'images={{.Images}}'      # images=0
( git ls-files -co --exclude-standard; echo infra/.env ) | sort -u | grep -v '^docs/' > files.txt
docker exec cr002-dind mkdir -p /work
tar -cf - -T files.txt infra/certs/server.crt infra/certs/server.key | docker exec -i cr002-dind tar -xf - -C /work
docker exec -e DOCKER_DEFAULT_PLATFORM=linux/amd64 -w /work/infra cr002-dind sh -c \
  'docker compose -p cr002-fresh build && docker compose -p cr002-fresh up -d && docker compose -p cr002-fresh ps -a'
```

The tree is the branch's version-controlled and untracked-not-ignored files, with a temporary
`.env` (generated keys) and the gitignored development certificate pair. It predates the
`BotoCoreError` edit to `backend/app/core/object_store_init.py`; that edit touches no image
reference, Dockerfile, lock file or base image, so it cannot change what is pulled or built (QA
accepted this for CR-002 AC-9, local part). Result: SeaweedFS, postgres, redis and nginx were
pulled by digest, the other images built from the repository; build and `up -d` exited 0 (about
2 min 30 s); `object-store` healthy, `weed version` printed `4.51 … linux amd64`,
`object-store-init` printed "object-store init ok: bucket medhub private, AES256" and `backend`
started. No cached image was involved, so the failure this report describes (a pinned reference
that no registry serves) no longer occurs. CI evidence on a hosted amd64 runner is TASK-179. The
`infra` project and `infra_minio_data` were not touched.

## Source

Raised by TASK-154, the first SOUP anomaly-list review (CR-001 D-4, AC-12), on 2026-10-22. The
evidence is in the "Anomaly list review" sections of SOUP-022 and SOUP-023.
