---
id: SOUP-011
type: soup
title: cryptography
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Python Cryptographic Authority (PyCA)
soup_version: 49.0.0
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-011 — cryptography 49.0.0

## Functional and performance requirements

AES-256-GCM authenticated field encryption at rest (SR-022) and key handling.

## Required hardware and software environment

Python 3.12; bundled OpenSSL; cffi 2.0.0.

Transitive dependencies covered by this record: cffi 2.0.0, bundled OpenSSL.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for cryptography 49.0.0 with cffi 2.0.0, pycparser 3.0 and the OpenSSL bundled in its wheels, the versions `backend/uv.lock` resolves. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database and https://github.com/pyca/cryptography/security/advisories; NVD; https://cryptography.io/en/latest/changelog/; OpenSSL vulnerabilities https://openssl-library.org/news/vulnerabilities/

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `cryptography` 49.0.0, `cffi` 2.0.0, `pycparser` 3.0.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `cryptography@49.0.0`, `cffi@2.0.0`.
- pyca/cryptography repository advisories — https://github.com/pyca/cryptography/security/advisories.
- NVD — CVE-2026-69247, https://nvd.nist.gov/vuln/detail/CVE-2026-69247.
- Changelog — https://cryptography.io/en/latest/changelog/, for 49.0.0 (2026-06-12) and the later releases 50.0.0 (2026-07-31), 50.0.1 (2026-08-25) and 50.0.2 (2026-09-30). There is no 49.0.x patch.
- OpenSSL vulnerabilities — https://openssl-library.org/news/vulnerabilities/, for the 4.0 branch from 2026-06 on.

### Findings

**One advisory applies to 49.0.0:** GHSA-g6cj-pr64-35w5 / CVE-2026-69247 / PYSEC-2026-3552 (high,
CVSS 4.0 AV:N/AC:H). `pkcs7_decrypt_der`, `pkcs7_decrypt_pem` and `pkcs7_decrypt_smime` reveal,
through distinguishable errors and timing, the result of unwrapping a `RecipientInfo`'s
`encryptedKey`. That is a Bleichenbacher oracle against the content-encryption key. Introduced in
44.0.0, fixed in 50.0.0.

The other recent repository advisories are fixed in or before 49.0.0: GHSA-jwv3-5hgf-82ww and
GHSA-m2h6-j472-rp4c (X.509 path building and name constraints, ≤ 48.0.0), GHSA-537c-gmf6-5ccf
(48.0.1) and earlier ones.

**Bundled OpenSSL.** The 49.0.0 entry does not name it. The last stated wheel build is OpenSSL
4.0.1 (48.0.1, 2026-06-09). 50.0.1 and 50.0.2 rebuild with 4.0.2 and 4.0.3. The OpenSSL advisories
fixed in 4.0.2 and 4.0.3 (2026-08 and 2026-09) concern CMS/PKCS#7, CMP, OCSP, QUIC, DTLS, the X.509
extension cache, and SM2 / non-NIST EC timing. The one AEAD item, CVE-2026-75803 (AEAD tag not
verified for empty ciphertext through `EVP_Cipher()`), is limited to ChaCha20-Poly1305 and AES-OCB.
`cffi` 2.0.0 and `pycparser` 3.0: none found.

### MedHub use and judgement

MedHub uses only `cryptography.hazmat.primitives.ciphers.aead.AESGCM`, for AES-256-GCM field
encryption at rest (`app/db/crypto.py`, SR-022, the RISK-011 design control). It uses no PKCS#7 or
S/MIME, no RSA and no X.509 API (checked 2026-10-22), so CVE-2026-69247 has no path into MedHub.
None of the OpenSSL advisories reaches AES-GCM. TLS is terminated by nginx (SOUP-024), and
Python's `ssl` module uses the base image's OpenSSL (SOUP-001), not this one. The RISK-011
encryption control is unaffected. Not hazard-relevant, MedHub not affected: no RISK. Recorded for
upgrade in [PRB-047](../problem-reports/PRB-047-runtime-transitives-with-published-advisories.md) (minor, 2026-10-22): move to 50.0.x at the next dependency change, in a separate
CR (CR-001 A-4).

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 49.0.0 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): CVE-2026-69247 (PKCS#7 decryption oracle, fixed in 50.0.0) applies to the version but not to MedHub's AES-GCM use; bundled-OpenSSL advisories reviewed; nothing hazard-relevant; recorded for upgrade in PRB-047 (minor). Record 1.0 → 1.1; approval record removed for re-review.
