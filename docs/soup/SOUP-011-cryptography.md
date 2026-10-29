---
id: SOUP-011
type: soup
title: cryptography
status: in_review
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-29"
manufacturer: Python Cryptographic Authority (PyCA)
soup_version: 50.0.2
anomaly_review: "2026-10-29"
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-011 — cryptography 50.0.2

## Functional and performance requirements

AES-256-GCM authenticated field encryption at rest (SR-022) and key handling.

## Required hardware and software environment

Python 3.12; bundled OpenSSL 4.0.3 (the 50.0.2 wheels are built with it, per the changelog; the installed wheel reports `OpenSSL 4.0.3 29 Sep 2026`); cffi 2.0.0; pycparser 3.0 (cffi's dependency).

Transitive dependencies covered by this record: cffi 2.0.0, pycparser 3.0, bundled OpenSSL 4.0.3. The 49.0.0 → 50.0.2 lock change moved no package other than `cryptography` (TASK-163).

## Anomaly list review

**Reviewed 2026-10-29** (TASK-163, CR-003 AC-14) for cryptography 50.0.2 with cffi 2.0.0, pycparser 3.0 and the OpenSSL 4.0.3 bundled in its wheels, the versions `backend/uv.lock` resolves. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database and https://github.com/pyca/cryptography/security/advisories; NVD; https://cryptography.io/en/latest/changelog/; OpenSSL vulnerabilities https://openssl-library.org/news/vulnerabilities/

### Sources checked

Same sources as the 2026-10-22 review, read on 2026-10-29:

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `cryptography` 50.0.2, `cffi` 2.0.0, `pycparser` 3.0. All three returned no vulnerability. The same query for `cryptography` 49.0.0 returned GHSA-g6cj-pr64-35w5 / PYSEC-2026-3552, which confirms that the query works and that the advisory no longer applies.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `cryptography@50.0.2`, `cffi@2.0.0` and `pycparser@3.0` returned no advisory. `cryptography@49.0.0` returned GHSA-g6cj-pr64-35w5.
- pyca/cryptography repository advisories — https://github.com/pyca/cryptography/security/advisories (published advisories listed through the REST API): the newest, GHSA-g6cj-pr64-35w5 and the two low-severity ones GHSA-jwv3-5hgf-82ww and GHSA-m2h6-j472-rp4c, were published on 2026-07-31. All three are fixed at or before 50.0.0. No advisory has been published since.
- NVD — CVE-2026-69247, https://nvd.nist.gov/vuln/detail/CVE-2026-69247: status "Awaiting Analysis", CVSS 4.0 base score 8.2 (high), no affected-product configuration yet. A keyword search for "pyca cryptography" and a CPE query for `cryptography` 50.0.2 returned no entry. NVD is therefore of limited use for this component, and OSV and the GitHub database carry the version-level finding.
- Changelog — https://cryptography.io/en/latest/changelog/, for 50.0.0 (2026-07-31), 50.0.1 (2026-08-25) and 50.0.2 (2026-09-30). 50.0.2 is the newest release; 51.0.0 is unreleased (`main`).
- OpenSSL vulnerabilities — https://openssl-library.org/news/vulnerabilities/, every entry affecting the 4.0 branch.

### Findings

**No anomaly applies to cryptography 50.0.2, cffi 2.0.0 or pycparser 3.0: none found.**

**Fixed since the previous review.** GHSA-g6cj-pr64-35w5 / CVE-2026-69247 / PYSEC-2026-3552
(PKCS#7 `EnvelopedData` decryption, a Bleichenbacher oracle through distinguishable errors and
timing; the GitHub Advisory Database rates it high, the repository advisory medium, NVD CVSS 4.0
8.2 high) is **fixed at 50.0.0**, and the 50.0.0 changelog confirms it. It does not apply at
50.0.2. The two low-severity advisories published with it (GHSA-jwv3-5hgf-82ww and
GHSA-m2h6-j472-rp4c, X.509 path building and name constraints) were already fixed at 49.0.0. The
PRB-047 finding for this item is therefore cleared.

**Changes 49.0.0 → 50.0.2 (changelog).** 50.0.0: the PKCS#7 fix, FFDH (finite-field
Diffie-Hellman) deprecation, stricter X.509, OCSP and ASN.1 parsing, new APIs. 50.0.1 and
50.0.2: wheels rebuilt with OpenSSL 4.0.2 and then 4.0.3, free-threaded wheels, PyO3 update. No
entry concerns AES-GCM or the `AESGCM` class.

**Bundled OpenSSL 4.0.3.** OpenSSL's vulnerability list shows no advisory with 4.0.3 as an
affected version. The latest ones affecting the 4.0 branch read "from 4.0.0 before 4.0.3": 14
advisories published 2026-09-29, all in code MedHub does not reach through `AESGCM`. They concern
QUIC (5), DTLS (2), timing in SM2 and non-NIST EC scalar multiplication (3), the X.509 extension
cache, relative CRLDP processing, CMP and `SSL_set_SSL_CTX()`. The AES-GCM-related OpenSSL entries are
in CMS/S/MIME `AuthEnvelopedData` and ASN.1 cipher-parameter handling, and in AES-SIV and
AES-GCM-SIV; MedHub uses none of them (it calls `AESGCM` only, with a raw 12-byte nonce, and no
CMS or ASN.1 API).

### MedHub use and judgement

MedHub uses only `cryptography.hazmat.primitives.ciphers.aead.AESGCM`, for AES-256-GCM field
encryption at rest (`app/db/crypto.py`, SR-022, the RISK-011 design control). The only import of
`cryptography` in `backend/app` and `backend/scripts` is that one (checked 2026-10-29). It uses
no PKCS#7 or S/MIME, no RSA and no X.509 API. TLS is terminated by nginx (SOUP-024), and
Python's `ssl` module uses the base image's OpenSSL (SOUP-001), not this one.

**Not hazard-relevant, MedHub not affected: no RISK, no PRB.** No unfixed anomaly exists at 50.0.2.

**Upgrade impact (§7.4).** The change in behaviour that matters to the RISK-011 / RISK-001
control is whether ciphertexts already at rest still decrypt. The known-answer test
`backend/tests/db/test_crypto_known_answer.py` (TS-008 TC-008.5) answers that: its fixed
envelope was produced under cryptography 49.0.0, and it decrypts and re-encrypts byte for byte
under 50.0.2.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 49.0.0 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): CVE-2026-69247 (PKCS#7 decryption oracle, fixed in 50.0.0) applies to the version but not to MedHub's AES-GCM use; bundled-OpenSSL advisories reviewed; nothing hazard-relevant; recorded for upgrade in PRB-047 (minor). Record 1.0 → 1.1; approval record removed for re-review.
- 2026-10-29 — 49.0.0 → 50.0.2; PRB-047, CR-003 (D-3), TASK-163. Second anomaly-list review, at the new version: no anomaly applies, and GHSA-g6cj-pr64-35w5 is fixed at 50.0.0. The lock moved only `cryptography` (cffi 2.0.0 and pycparser 3.0 unchanged); bundled OpenSSL moves to 4.0.3. Change analysis: the AES-GCM envelope is MedHub's own format over a fixed standard, and the known-answer test (TS-008 TC-008.5, ciphertext produced under 49.0.0) shows that data at rest still decrypts. Record 1.1 → 1.2; approval record removed for re-review.
