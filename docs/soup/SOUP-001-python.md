---
id: SOUP-001
type: soup
title: Python runtime
status: approved
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-23"
manufacturer: Python Software Foundation
soup_version: 3.12.15
anomaly_review: "2026-10-22"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-23"
approved_digest: d5d748f4c72a9e4f1548e4270639e5ed42e74a8f737351d6c154e756f174a1aa
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-001 — Python runtime 3.12.15

## Functional and performance requirements

Language runtime and standard library for every backend item, including `secrets` and `hashlib` for tokens and digests.

## Required hardware and software environment

Debian-based `python:3.12.15-slim` container image; base OS Debian GNU/Linux 13 (trixie) (A-5: the base OS is part of this item, identified by the digest).

| Full image reference | Used by |
|---|---|
| `python:3.12.15-slim@sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2` | `backend/Dockerfile`: builder stage and runtime stage (identical reference) |

Resolved on 2026-10-22 with `docker buildx imagetools inspect python:3.12-slim` and `docker buildx imagetools inspect python:3.12.15-slim`; both reported the same image configuration (`PYTHON_VERSION=3.12.15`). The digest is the multi-arch image index digest (`Digest:` line of the second command). Tests ran on CPython 3.12.3.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) by the Software Architect role, at the pinned
version `python:3.12.15-slim@sha256:cb33f7f7…11d2` (CPython 3.12.15; base OS Debian GNU/Linux 13,
`base-files` 13.8+deb13u7; bundled pip 25.0.1).

Sources checked:

| Source | URL | What was checked |
|---|---|---|
| Python 3.12.15 release page (vendor) | https://www.python.org/downloads/release/python-31215/ | Release date (2026-09-30), the ten security fixes it lists, security-only status (fixes until October 2028, PEP 693) |
| CVEs issued by the PSF CNA, via NVD CVE API 2.0 | https://services.nvd.nist.gov/rest/json/cves/2.0?sourceIdentifier=cna@python.org | Published 2026-08-15..2026-10-22 (9 CVEs), each checked against the 3.12.15 fix list |
| CPython repository, `3.12` branch history (vendor) | https://github.com/python/cpython/commits/3.12 | Whether the fix for each CVE not listed on the release page is in tag `v3.12.15` |
| CPython GitHub Security Advisories | https://github.com/python/cpython/security/advisories | No advisory published in 2026 |
| OSV (Debian:13), from the Debian security tracker | https://api.osv.dev/v1/querybatch | Every source package of the image (61) at its installed version |
| OSV (PyPI) | https://api.osv.dev/v1/query | pip 25.0.1, bundled in the image |

Method for the base OS: `/var/lib/dpkg/status` was copied out of the pinned image without running
it (`docker create` + `docker cp`), and each source package was queried in OSV at its installed
version. The bundled packages were listed from `site-packages` the same way. `docker scout cves`
was tried (CLI 0.20.0) and crashed, so no image scanner was used.

Findings:

| ID | Summary | Fixed in | Applies to 3.12.15 | MedHub affected | Hazard relevance |
|---|---|---|---|---|---|
| CVE-2026-12345 (gh-157579) | Race in `tempfile.TemporaryDirectory` cleanup: an attacker who can modify the tree can redirect deletion or permission resets outside it | 3.15/3.14/main backports exist. The `[3.12]` backport (458e7134) was reverted as "prematurely merged" (e1f3590f) before the `v3.12.15` tag. No 3.12 fix as of 2026-10-22 | Yes | No: no backend module uses `tempfile`. Exploitation needs write access to the container filesystem | None |
| pip 25.0.1: CVE-2025-8869, CVE-2026-1703, CVE-2026-3219, CVE-2026-6357, CVE-2026-8643, CVE-2026-13346 | Path traversal and archive-confusion issues when pip installs packages | pip 25.3–26.2 | Yes (pip is part of the image) | Build time only: `backend/Dockerfile` runs `pip install uv` in the builder stage. The runtime never calls pip. The unpinned `pip install uv` is already PRB-034 (CR-001 D-2) | None at runtime; a build-supply-chain concern under PRB-034 |

The other eight PSF CVEs of the period (CVE-2026-19445, CVE-2026-19553, CVE-2026-82049,
CVE-2026-15310, CVE-2026-19672, CVE-2026-15806, CVE-2026-17084, CVE-2026-87910) are fixed in
3.12.15, which also bundles Expat 2.8.5 (gh-157953).

Base OS: OSV lists 69 entries against 18 of the 61 source packages (for example `glibc`
2.41-12+deb13u4, `sqlite3`, `systemd`, `util-linux`, `tar`, `perl`, `zlib`). **None has a fix in
Debian 13** at the date of the review: the Debian tracker marks each one "unimportant" or "not yet
assigned". The image therefore carries every security update Debian 13 had published. OpenSSL
3.5.7-1~deb13u3 has no open entry.

Hazard relevance: none. The functions the backend relies on (`secrets`, `hashlib`, the language
runtime) are not named by any anomaly. Python's `ssl` server path (CVE-2026-19445) is not used,
because TLS terminates at nginx (SOUP-024). Note for monitoring: 3.12 is in its security-only
phase. Non-security bugs are no longer fixed in this line, and a security fix reaches it only as
a source release such as 3.12.15.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — `python:3.12-slim` → `python:3.12.15-slim@sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2`; pinned at the version the tag resolved to, no upgrade (CR-001 A-4, TASK-155); PRB-001.
- 2026-10-22 — Version 1.2: first anomaly-list review at 3.12.15 (TASK-154, CR-001 AC-11): one
  unfixed CPython CVE (CVE-2026-12345, `tempfile`) and six pip 25.0.1 advisories apply. None affects
  MedHub's runtime, none is hazard-relevant. `anomaly_review` set. No version change. Approval
  record cleared for re-approval.
