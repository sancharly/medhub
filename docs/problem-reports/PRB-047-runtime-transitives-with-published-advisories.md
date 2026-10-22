---
id: "PRB-047"
type: problem-report
title: "Locked runtime dependencies carry published advisories that do not affect MedHub's use"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
criticality: minor
links: []
tags: ["soup", "maintenance", "security"]
---

# PRB-047 — Locked runtime dependencies carry published advisories that do not affect MedHub's use

## Observed

The first SOUP anomaly-list review found published advisories against three packages at the
versions `backend/uv.lock` resolves:

| Package (SOUP record) | Advisories | Fixed in | Why MedHub is not affected |
|---|---|---|---|
| anyio 4.14.0, a transitive of Starlette ([SOUP-003](../soup/SOUP-003-starlette.md)) | GHSA-3w57-8xmc-8v26 / CVE-2026-63349: `run_process`/`open_process` ignore `extra_groups`. GHSA-5p39-cfhj-2xmp / CVE-2026-64847: process-pool workers can block on undrained stderr. GHSA-82r6-8w77-94w6 / CVE-2026-63374: `TLSStream` encodes host names with IDNA 2003 | 4.14.2 | No backend module imports anyio. Starlette uses it only for its thread pool: no subprocesses, no process pool, no anyio TLS client stream. TLS terminates at nginx (SOUP-024) |
| urllib3 2.7.0, a transitive of boto3 ([SOUP-019](../soup/SOUP-019-boto3.md)) | GHSA-8988-9cw3-xx77 / CVE-2026-97687: HTTPS-proxy TLS configuration may be ignored. GHSA-vxq7-64xx-v4gw / CVE-2026-97689: unbounded chunk-size line in `stream()`/`read_chunked()`. GHSA-gh4c-6fx4-qh6g / CVE-2026-97688: chunked deflate streaming can loop forever | 2.8.0 | No proxy is configured. The two availability flaws need the object store (`http://minio:9000`, internal network) to send hostile responses. That would first require compromising MinIO, the scenario of RISK-012/PRB-043, and the only added effect is a hung API worker (RISK-007, covered by the healthcheck and restart policy) |
| cryptography 49.0.0 ([SOUP-011](../soup/SOUP-011-cryptography.md)) | GHSA-g6cj-pr64-35w5 / CVE-2026-69247: Bleichenbacher oracle in `pkcs7_decrypt_der`/`_pem`/`_smime` | 50.0.0 | MedHub uses only `AESGCM` (`backend/app/db/crypto.py`, SR-022). It uses no PKCS#7, S/MIME, RSA or X.509 API |

## Impact

None on MedHub's behaviour today. The locked versions stay exposed until the next dependency
change, and a future change that starts using an affected API would inherit the flaw without
noticing.

## Safety evaluation

Not hazard-relevant: no path from MedHub's use to any of the advisories, as judged in SOUP-003,
SOUP-011 and SOUP-019. The RISK-011 field-encryption control (AES-256-GCM) and the SSE request
path are unaffected. Criticality is `minor`: it is a patch-currency obligation (§6.1 f), not a
realized defect.

Released versions (§9.3): no `release` record exists (`docs/releases/` is absent), so no released
version in use is affected and no notification is needed.

## Proposed resolution

At the next dependency change, in a separate CR (CR-001 A-4 forbids upgrades):

- Raise anyio to ≥ 4.14.2, urllib3 to ≥ 2.8.0 and cryptography to ≥ 50.0.0. Apply `uv lock`
  only for these packages and check the lock diff.
- Re-run the backend suite (including the TS-008 encryption tests) and the anomaly review for
  the new versions.
- Update SOUP-003, SOUP-011 and SOUP-019.

## Source

Raised by TASK-154, the first SOUP anomaly-list review (CR-001 AC-12, backend slice), on
2026-10-22. The evidence is in the "Anomaly list review" sections of SOUP-003, SOUP-011 and
SOUP-019.
