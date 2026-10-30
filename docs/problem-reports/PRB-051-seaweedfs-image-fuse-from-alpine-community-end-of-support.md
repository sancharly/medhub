---
id: "PRB-051"
type: problem-report
title: "SeaweedFS image ships fuse from Alpine v3.24 community, whose support ends 2026-11-01"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
criticality: minor
links: []
tags: ["soup", "infrastructure", "end-of-support"]
---

# PRB-051 — SeaweedFS image ships fuse from Alpine v3.24 community, whose support ends 2026-11-01

## Observed

The pinned SeaweedFS image (SOUP-036, `chrislusf/seaweedfs:4.51@sha256:f7a49e3f…134b8`) is built
on Alpine v3.24.3. One of its 29 apk packages, `fuse` 2.9.9, comes from the v3.24 `community`
repository (checked with `apk policy`). https://alpinelinux.org/releases.json, read 2026-10-30,
lists the end date of v3.24 `community` as **2026-11-01**; the `main` repository is supported
until 2028-06-01. Found during the TASK-172 anomaly review and confirmed by QA (CR-002, candidate
P-1).

## Impact

Under the PLAN-002 end-of-support rule (less than 12 months left, or support already ended), this
is a shortfall. After 2026-11-01, fixes for `fuse` in v3.24 are no longer guaranteed.

## Investigation

The upstream Dockerfile's final stage is an unpinned `alpine` (`docker/Dockerfile.go_build`, tag
4.51), so the base OS is whatever Alpine release was current when upstream built 4.51, and
`fuse` is installed for SeaweedFS's optional FUSE mount (`weed mount`). MedHub runs the image
with `weed server …` only and mounts no FUSE file system in the container (SOUP-036,
"Environment"), so the package is installed but never exercised.

## Safety evaluation

No hazard is realized: the package is not used by MedHub, it is not reachable from the S3
endpoint, and the object store is reachable only by the backend and the bucket initialiser
(TASK-177). It affects no data integrity, safety-related function or clinical decision. No
released version is affected (no release has shipped SeaweedFS), so no notification is needed.
Hence `minor`. It does not block the release gate.

## Proposed resolution

Upstream rebuilds the image on a newer Alpine with each release. Move to a SeaweedFS release whose
image has no `community` package past its support end date, through the reviewed digest change of
the PLAN-002 1.2 monthly rule for SOUP-036. If no such release is adopted before the next release,
record here why the release may ship with it (PLAN-002, "On a shortfall"). Needs a task and a CR;
not in CR-002's scope (human decision, 2026-10-30).

## Source

Raised by the human on 2026-10-30 from CR-002 PRB candidate P-1 (TASK-172 anomaly review, QA
review of TASK-172).
