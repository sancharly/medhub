---
id: SOUP-024
type: soup
title: nginx
status: approved
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-23"
manufacturer: F5, Inc. / nginx authors
soup_version: 1.31.8
anomaly_review: "2026-10-22"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-23"
approved_digest: 9c567d092e01183ee86caa8331290cd2520c808d04bde37a7b5dc3e26cd41026
approval_note: self-approved
links: []
tags:
  - soup
  - layer:infrastructure
  - class:B
---

# SOUP-024 — nginx 1.31.8

## Functional and performance requirements

TLS termination, HSTS and security headers at the reverse proxy (SR-001, SR-031), and static serving of the frontend bundle.

## Required hardware and software environment

`nginx:1.31.8-alpine` container image; base OS Alpine Linux v3.24 (A-5); certificates in `infra/certs/`.

| Full image reference | Used by |
|---|---|
| `nginx:1.31.8-alpine@sha256:e2d97c2b8c016f12c2f1a27d095685063b2f281c4edf2babfde6001cf4fb77a8` | `infra/docker-compose.yml`: `reverse-proxy` service; `frontend/Dockerfile`: runtime stage (identical reference) |

Resolved on 2026-10-22 with `docker buildx imagetools inspect nginx:alpine` and `docker buildx imagetools inspect nginx:1.31.8-alpine`; both reported the same image configuration (`NGINX_VERSION=1.31.8`). The digest is the multi-arch image index digest (`Digest:` line of the second command). The tag `nginx:alpine` and `nginx:1.31.8-alpine` had the same image configuration but different index digests that day (`nginx:alpine` = `sha256:060849a174666c53439dc7cecbf8f67e225c7cbfb1a44ca97915d9a172a81e6d`); the full-release tag's digest is pinned.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) by the Software Architect role, at the pinned
version `nginx:1.31.8-alpine@sha256:e2d97c2b…a8` (nginx 1.31.8, mainline branch; base OS Alpine
Linux 3.24.3).

Sources checked:

| Source | URL | What was checked |
|---|---|---|
| nginx security advisories (vendor) | https://nginx.org/en/security_advisories.html | Every advisory listed, with its vulnerable and not-vulnerable ranges (26 advisories with 2026 CVE IDs) |
| nginx CHANGES (vendor release notes) | https://nginx.org/en/CHANGES | 1.31.0–1.31.8 "Security:" entries; 1.31.8 (21 Oct 2026) is the newest release and has none |
| NVD CVE API 2.0 | https://services.nvd.nist.gov/rest/json/cves/2.0 | Keyword `nginx`, published 2026-07-01..2026-10-22 (102 results, filtered to NGINX Open Source) |
| OSV (Alpine:v3.24) | https://api.osv.dev/v1/querybatch | Every source package of the image (60 source / 72 binary packages) at its installed version |

Method for the base OS: the package database `/lib/apk/db/installed` was copied out of the pinned
image without running it (`docker create` + `docker cp`), and each source package was queried in
OSV at its installed version. `docker scout cves` was tried on the digest; the installed CLI
(0.20.0) crashed and gave no result, so no image scanner was used. nginx itself comes from the
nginx.org Alpine repository, not from Alpine, so it is covered by the vendor sources above, not by
OSV Alpine.

Findings: **none found** for nginx 1.31.8. Every 2026 advisory on the vendor page is fixed in
1.31.7 or earlier (the newest, CVE-2026-15176, CVE-2026-93479, CVE-2026-95101, CVE-2026-97629 and
CVE-2026-97205, in 1.31.7 of 14 Oct 2026). Base OS: OSV returned no entry for any package at its
installed version, including OpenSSL 3.5.9-r0, which carries the OpenSSL fixes of 29 Sep 2026.

Two NGINX JavaScript (njs) advisories (CVE-2026-78222, CVE-2026-101019) were not mapped to a
version. They do not apply to MedHub: the image ships `nginx-module-njs` 1.31.8.1.0.2 but neither
`infra/reverse-proxy/nginx.conf` nor `frontend/nginx.conf` loads a dynamic module.

Hazard relevance: none. The controls this item carries (TLS 1.2+, HTTP→HTTPS redirect, HSTS and
security headers, SR-001 and SR-031; RISK-005, RISK-010, RISK-011) depend on no anomalous
function. MedHub's configuration uses `ssl_protocols`, `ssl_ciphers`, `add_header` and
`proxy_pass` only; it uses none of the modules named in the 2026 advisories (map with regex,
alias with rewrite, SSI, slice, HTTP/3, AIO, TLS session ticket rotation).

Observation for monitoring: 1.31 is the mainline branch, so a fix arrives only as the next 1.31.x
release, typically within weeks of the previous one. The cadence in PLAN-002 (at every dependency
change, before every release, at most 365 days apart) is the minimum. Three security releases
appeared between 1.31.3 and 1.31.7.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — `nginx:alpine` → `nginx:1.31.8-alpine@sha256:e2d97c2b8c016f12c2f1a27d095685063b2f281c4edf2babfde6001cf4fb77a8`; pinned at the version the tag resolved to, no upgrade (CR-001 A-4, TASK-155); PRB-001.
- 2026-10-22 — Version 1.2: first anomaly-list review at 1.31.8 (TASK-154, CR-001 AC-11): none
  found, no hazard-relevant anomaly. `anomaly_review` set. No version change. Approval record
  cleared for re-approval.
