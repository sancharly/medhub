---
id: "PRB-039"
type: problem-report
title: "Bucket initialisation runs before MinIO accepts connections"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-30"
criticality: minor
links: []
tags: ["infrastructure", "verification"]
---

# PRB-039 — Bucket initialisation runs before MinIO accepts connections

## Observed

In `infra/docker-compose.yml` the one-shot `createbuckets` service depends on `minio` with
`condition: service_started`, and `minio` has no healthcheck. On `docker compose up -d` the `mc`
container starts while MinIO is still initialising and its three commands fail with
`connection refused` (alias set, `mc mb`, `mc anonymous set`); the entrypoint ends with `exit 0`, so
the failure is silent at the Compose level. Observed on 2026-10-22 during TASK-155 verification of the
pinned stack. The compose dependency is unchanged by CR-001, so the pre-pinning stack has the same
race; it was not captured in the baseline run.

## Impact

On a fresh `minio_data` volume the `medhub` bucket is not created, and attachment storage (SR-013)
fails until the bucket is created by hand. On an existing volume (as on the reference workstation,
where the bucket already existed) the failure is hidden.

## Investigation

Root cause: `createbuckets` waits for `minio` with `condition: service_started`
(`infra/docker-compose.yml:115-117`), which only means that the container process was created, and
`minio` defines no healthcheck. The entrypoint (`infra/docker-compose.yml:118-124`) runs `mc alias
set`, `mc mb` and `mc anonymous set` once, each of which fails with `connection refused` while the
server initialises, and ends with `exit 0;`, which hides the failure. On a fresh volume the bucket is
never created.

## Safety evaluation

No hazard is realized: the failure is loud at first use (attachment unavailable, RISK-007), and no
data is stored unencrypted. Hence `minor`.

## Proposed resolution

Give `minio` a healthcheck and make `createbuckets` depend on `service_healthy`, or retry the alias
command until it succeeds, and make the entrypoint fail when bucket creation fails. Needs a task and
a CR.

## Source

Found by the software developer while running TASK-155 verification (AC-5); out of scope for CR-001.
