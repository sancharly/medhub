---
id: SOUP-019
type: soup
title: boto3
status: in_review
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Amazon Web Services
soup_version: 1.43.117
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-019 — boto3 1.43.117

## Functional and performance requirements

S3 API client used by `ObjectStorageClient` to store and fetch attachment objects with server-side encryption (SR-013, SR-022).

## Required hardware and software environment

Python 3.12; botocore; a MinIO or S3 endpoint (SOUP-022).

Declared as a required runtime dependency: `"boto3>=1.43.0"` under `[project] dependencies` in
`backend/pyproject.toml`, resolved by `backend/uv.lock` to boto3 1.43.117 and installed in the
production image by `uv sync --frozen --no-dev` (`backend/Dockerfile`).

Transitive dependencies covered by this record, at the versions locked in `backend/uv.lock`:
botocore 1.43.117, s3transfer 0.19.3, jmespath 1.1.0. Its other dependencies, `python-dateutil` and
`urllib3`, were already locked for other components and are unchanged. In the production image,
though, urllib3 2.7.0 is present only because of botocore: the other lock entries that pull it in
(docker, requests, testcontainers) are dev-only. This record therefore covers urllib3 2.7.0, and
python-dateutil 2.9.0.post0 with six 1.17.0 (also required by Celery, SOUP-014).

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for boto3 1.43.117 and the transitive dependencies `backend/uv.lock` resolves for it: botocore 1.43.117, s3transfer 0.19.3, jmespath 1.1.0, urllib3 2.7.0, python-dateutil 2.9.0.post0 and six 1.17.0. Priority item: it carries the SSE request since PRB-002. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database and the boto/boto3, boto/botocore, boto/s3transfer, jmespath/jmespath.py and urllib3/urllib3 repository advisories; NVD; https://raw.githubusercontent.com/boto/botocore/develop/CHANGELOG.rst

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `boto3` 1.43.117, `botocore` 1.43.117, `s3transfer` 0.19.3, `jmespath` 1.1.0, `urllib3` 2.7.0, `python-dateutil` 2.9.0.post0, `six` 1.17.0.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `boto3@1.43.117`, `botocore@1.43.117`, `s3transfer@0.19.3`, `jmespath@1.1.0`, `urllib3@2.7.0`.
- Repository advisories — https://github.com/boto/boto3/security/advisories, https://github.com/boto/botocore/security/advisories, https://github.com/boto/s3transfer/security/advisories, https://github.com/jmespath/jmespath.py/security/advisories, https://github.com/urllib3/urllib3/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keywords `boto3`, `botocore`, `s3transfer`, `jmespath`; and CVE-2026-97687/97688/97689 (https://nvd.nist.gov/vuln/detail/CVE-2026-97689).
- Changelog — https://raw.githubusercontent.com/boto/botocore/develop/CHANGELOG.rst (1.43.117, 1.43.116 and the 1.43.x bugfix entries). boto3, botocore and s3transfer at these versions are the latest releases (2026-10-19/21).

### Findings

**boto3, botocore, s3transfer, jmespath, python-dateutil, six: none found** on 2026-10-22. NVD's
matches for these keywords are other products (jmespath.php, Kyverno, MaxKB) or an old urllib3 CVE
(CVE-2025-50181, fixed in urllib3 2.5.0). botocore 1.43.117 adds API-model changes and one bugfix,
the removal of the "AAA Certificate Services" root from its vendored CA bundle. 1.43.115 fixed a
`ResponseStreamingError` regression with urllib3 v2, and 1.43.117 includes that fix.

**urllib3 2.7.0: three advisories, all fixed in 2.8.0** (2026-09-15):

| ID | Summary | Affected | MedHub affected? |
|---|---|---|---|
| GHSA-8988-9cw3-xx77 / CVE-2026-97687 (high) | HTTPS-proxy TLS configuration may be ignored or overridden | 1.26.0 to < 2.8.0 | No: no proxy is configured. The endpoint is `http://minio:9000` on the internal Compose network |
| GHSA-vxq7-64xx-v4gw / CVE-2026-97689 (high, availability) | `HTTPResponse.stream()`/`read_chunked()` buffers an unbounded chunk-size line | 1.10.3 to < 2.8.0 | Code path present (`get_object` reads the body through urllib3). Needs a hostile object-store response |
| GHSA-gh4c-6fx4-qh6g / CVE-2026-97688 (moderate, availability) | Chunked deflate streaming can loop forever | 2.6.2 to < 2.8.0 | As above: needs a hostile object-store response |

### MedHub use and judgement

`ObjectStorageClient` (`app/core/object_storage.py`, SI-ATTACH) calls `put_object` with
`ServerSideEncryption="AES256"`, `get_object` and `delete_object` directly against MinIO (SR-013,
SR-022; the RISK-011 SSE control, RISK-007 availability). It uses no managed transfers (so
s3transfer is not exercised), no waiters or paginators (jmespath), and no proxy. No anomaly touches
the SSE request. The two urllib3 availability flaws need MinIO (SOUP-022), which sits inside
MedHub's own network, to send crafted responses. A compromised object store already exposes the
stored objects, and RISK-001/RISK-011 consider storage access; the only extra effect would be a
hung or memory-exhausted API worker (RISK-007, covered by the healthcheck and restart policy). Not
hazard-relevant, and no MedHub behaviour is affected: no RISK. Recorded for upgrade in [PRB-047](../problem-reports/PRB-047-runtime-transitives-with-published-advisories.md)
(minor, 2026-10-22): raise urllib3 to 2.8.0 or later at the next dependency change, in a separate
CR (CR-001 A-4). The hostile-object-store precondition is the scenario of RISK-012 and PRB-043.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — undeclared → 1.43.117; declared as a required dependency (PRB-002, CR-001, TASK-157).
  Locked with botocore 1.43.117, s3transfer 0.19.3 and jmespath 1.1.0; no other locked package
  changed (CR-001 A-4). `ObjectStorageClient` is built from the real SDK by
  `backend/tests/test_object_storage.py`, and `import boto3` is checked in the production image by
  the Docker Build job (TS-007 TC-007.5, TS-013 TC-013.8). The anomaly-list review of this version
  is TASK-154.
- 2026-10-22 — 1.43.117 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): boto3/botocore/s3transfer/jmespath none found; urllib3 2.7.0 (runtime transitive) has three advisories fixed in 2.8.0, applicable only with a hostile object store or an HTTPS proxy; nothing hazard-relevant, recorded for upgrade in PRB-047 (minor); environment section corrected for urllib3. Record 1.1 → 1.2; approval record removed for re-review.
