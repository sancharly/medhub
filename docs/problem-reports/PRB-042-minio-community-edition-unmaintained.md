---
id: "PRB-042"
type: problem-report
title: "MinIO community edition is unmaintained and its images can no longer be obtained"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
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

## Source

Raised by TASK-154, the first SOUP anomaly-list review (CR-001 D-4, AC-12), on 2026-10-22. The
evidence is in the "Anomaly list review" sections of SOUP-022 and SOUP-023.
