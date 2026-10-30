---
id: SOUP-019
type: soup
title: boto3
status: approved
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-30"
manufacturer: Amazon Web Services
soup_version: 1.43.117
anomaly_review: "2026-10-29"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-30"
approved_digest: f7836e09b4e9b397e3b178aa12d7bf77cb4ebfd13c367727ecbc7b8a371e4cd4
approval_note: self-approved
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
`urllib3`, are also locked. In the production image, urllib3 2.8.0 is present only because of
botocore: the other lock entries that pull it in (docker, requests, testcontainers) are dev-only.
This record therefore covers urllib3 2.8.0 (moved from 2.7.0 by TASK-164, the only locked version
that changed for this record), and python-dateutil 2.9.0.post0 with six 1.17.0 (also required by
Celery, SOUP-014).

## Anomaly list review

**Reviewed 2026-10-29** (TASK-164, CR-003 AC-14) for boto3 1.43.117 and the transitive dependencies `backend/uv.lock` resolves for it: botocore 1.43.117, s3transfer 0.19.3, jmespath 1.1.0, urllib3 2.8.0, python-dateutil 2.9.0.post0 and six 1.17.0. Priority item: it carries the SSE request since PRB-002. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database and the boto/boto3, boto/botocore, boto/s3transfer, jmespath/jmespath.py and urllib3/urllib3 repository advisories; NVD; https://raw.githubusercontent.com/urllib3/urllib3/main/CHANGES.rst

### Sources checked

Same sources as the 2026-10-22 review, read on 2026-10-29:

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `boto3` 1.43.117, `botocore` 1.43.117, `s3transfer` 0.19.3, `jmespath` 1.1.0, `urllib3` 2.8.0, `python-dateutil` 2.9.0.post0 and `six` 1.17.0 each returned no vulnerability. The same query for `urllib3` 2.7.0 returned GHSA-8988-9cw3-xx77, GHSA-vxq7-64xx-v4gw and GHSA-gh4c-6fx4-qh6g (with their PYSEC aliases), which confirms that the query works and that those advisories no longer apply.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `boto3@1.43.117`, `botocore@1.43.117`, `s3transfer@0.19.3`, `jmespath@1.1.0` and `urllib3@2.8.0` returned no advisory. `urllib3@2.7.0` returned the same three.
- Repository advisories — https://github.com/boto/boto3/security/advisories, https://github.com/boto/botocore/security/advisories, https://github.com/boto/s3transfer/security/advisories, https://github.com/jmespath/jmespath.py/security/advisories, https://github.com/urllib3/urllib3/security/advisories. The urllib3 list (read through the REST API) holds GHSA-8988-9cw3-xx77, GHSA-vxq7-64xx-v4gw and GHSA-gh4c-6fx4-qh6g (all published 2026-09-15, patched version 2.8.0), and GHSA-mf9v-mfxr-j63j and GHSA-qccp-gfcp-xxvc (published 2026-05-07, patched version 2.7.0, already fixed in the version of the previous review). None is published against 2.8.0.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keywords `urllib3` and `botocore`; and CVE-2026-97687/97688/97689 (https://nvd.nist.gov/vuln/detail/CVE-2026-97689, "Analyzed", CVSS 4.0 score 8.9). The new entries for these keywords are other products that use urllib3 or botocore (MCP Atlassian CVE-2026-77242, MaxKB CVE-2026-79916), not defects in these components.
- Changelog — https://raw.githubusercontent.com/urllib3/urllib3/main/CHANGES.rst, entry 2.8.0 (2026-09-15). boto3, botocore and s3transfer are unchanged, so their changelog review of 2026-10-22 stands.

### Findings

**boto3, botocore, s3transfer, jmespath, python-dateutil, six: none found** on 2026-10-29, the
same as on 2026-10-22.

**urllib3 2.8.0: none found.** The three advisories of the 2026-10-22 review (PRB-047) are
**fixed at 2.8.0**, and the 2.8.0 changelog lists each one under "Security":

| ID | Summary | Affected | Status at 2.8.0 |
|---|---|---|---|
| GHSA-8988-9cw3-xx77 / CVE-2026-97687 (high) | HTTPS-proxy TLS configuration may be ignored or overridden | 1.26.0 to < 2.8.0 | **Fixed in 2.8.0** |
| GHSA-vxq7-64xx-v4gw / CVE-2026-97689 (high, availability) | `HTTPResponse.stream()`/`read_chunked()` buffers an unbounded chunk-size line | 1.10.3 to < 2.8.0 | **Fixed in 2.8.0** |
| GHSA-gh4c-6fx4-qh6g / CVE-2026-97688 (moderate, availability) | Chunked deflate streaming can loop forever | 2.6.2 to < 2.8.0 | **Fixed in 2.8.0** |

**Behaviour changes in 2.8.0 (changelog).** The first fix changes how HTTPS proxies take their TLS
configuration (proxy CA and client certificates now come from `proxy_ssl_context`, and destination
settings no longer apply to HTTPS forwarding proxies). **Not applicable:** no proxy is configured;
the endpoint is `http://minio:9000` on the internal Compose network. 2.8.0 also deprecates an
empty `Retry` `allowed_methods` (botocore uses its own retry handler, not this option), folds
obsolete folded header lines into spaces, and adds `Url` and `make_headers` helpers. None changes
how botocore sends or reads an S3 request.

The other 2.8.0 changes that apply to plain-HTTP connection pools were reviewed and are not
applicable or harmless here: `ConnectionPool.pool` resolves `LifoQueue` from `queue` late (only
matters when it is monkey-patched, e.g. by gevent; MedHub does not); `drain_conn()` discards
unread data in 64 KiB chunks (a performance detail of releasing a connection); URL parsing
enforces RFC 3986 host syntax more strictly (the host is the fixed `minio` from configuration, so
nothing is rejected); and a retried request whose body has `tell()` but not `seek()` raises
`UnrewindableBodyError` instead of `ValueError` (the upload body is a seekable `BytesIO`, and
botocore does its own retries). The remaining entries concern proxies, SOCKS, pyOpenSSL, HTTP/2,
redirects and fingerprint assertions, none of which MedHub uses.

### MedHub use and judgement

`ObjectStorageClient` (`app/core/object_storage.py`, SI-ATTACH) calls `put_object` with
`ServerSideEncryption="AES256"`, `get_object` and `delete_object` directly against MinIO (SR-013,
SR-022; the RISK-011 SSE control, RISK-007 availability). It uses no managed transfers (so
s3transfer is not exercised), no waiters or paginators (jmespath), and no proxy. No anomaly applies
to the locked versions, so none touches the SSE request. Not hazard-relevant, and no MedHub
behaviour is affected: no RISK, no PRB. PRB-047 is resolved for this item. The hostile-object-store
precondition of the former urllib3 findings was the scenario of RISK-012 and PRB-043, and it is
now moot for these three advisories.

**Upgrade impact (§7.4).** urllib3 only carries the request: the `ServerSideEncryption` header is
set by botocore and passes through unchanged, and a transport regression fails the upload or
download loudly (RISK-007); it cannot store an object in plaintext. No automated test sends a real
request to MinIO (PRB-036), so the evidence is the instantiation test
(`backend/tests/test_object_storage.py`, TS-007 TC-007.5) and a manual attachment round trip on
the rebuilt Compose stack (TASK-164): upload of a 307,200-byte file to a clinical entry through
`https://localhost` returned 201, the download returned 200, and the downloaded bytes were
identical (same SHA-256). End-to-end proof of SSE on the stored object stays PRB-036's.

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
- 2026-10-29 — urllib3 2.7.0 → 2.8.0 (transitive); boto3 1.43.117 unchanged; PRB-047, CR-003 (D-3), TASK-164. Second anomaly-list review, at the new version: no anomaly applies, and the three urllib3 advisories are fixed at 2.8.0. The lock moved only urllib3 (and anyio, SOUP-003); botocore, s3transfer, jmespath, python-dateutil and six unchanged. Change analysis: the 2.8.0 HTTPS-proxy behaviour change does not apply (no proxy); the manual attachment round trip on the rebuilt stack confirms the request path. Record 1.2 → 1.3; approval record removed for re-review.
