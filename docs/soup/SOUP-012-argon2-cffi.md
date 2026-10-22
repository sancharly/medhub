---
id: SOUP-012
type: soup
title: argon2-cffi
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Hynek Schlawack
soup_version: 25.1.0
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-012 — argon2-cffi 25.1.0

## Functional and performance requirements

Argon2id password hashing and verification with constant-time comparison (SR-002, SR-025, SR-029).

## Required hardware and software environment

Python 3.12; argon2-cffi-bindings 25.1.0 (bundled libargon2).

Transitive dependencies covered by this record: argon2-cffi-bindings 25.1.0.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for argon2-cffi 25.1.0 with argon2-cffi-bindings 25.1.0 (vendored phc-winner-argon2 at commit `f57e61e`) and cffi 2.0.0, the versions `backend/uv.lock` resolves. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database, https://github.com/hynek/argon2-cffi/security/advisories and https://github.com/hynek/argon2-cffi-bindings/security/advisories; NVD; https://github.com/hynek/argon2-cffi/releases/tag/25.1.0; https://github.com/hynek/argon2-cffi-bindings/blob/main/CHANGELOG.md

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `argon2-cffi` 25.1.0, `argon2-cffi-bindings` 25.1.0, `cffi` 2.0.0.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `argon2-cffi@25.1.0`, `argon2-cffi-bindings@25.1.0`.
- Repository advisories — https://github.com/hynek/argon2-cffi/security/advisories and https://github.com/hynek/argon2-cffi-bindings/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keyword `argon2`.
- Release notes — https://github.com/hynek/argon2-cffi/releases/tag/25.1.0 (no later argon2-cffi release) and https://github.com/hynek/argon2-cffi-bindings/blob/main/CHANGELOG.md (25.1.0, and 26.1.0 of 2026-08-20). The vendored Argon2 commit is from https://pypi.org/project/argon2-cffi-bindings/.

### Findings

**None found** on 2026-10-22. No advisory for argon2-cffi, argon2-cffi-bindings or cffi in OSV, the
GitHub Advisory Database or either repository. NVD's `argon2` matches are other implementations
or products (Crypt::Argon2 for Perl, Bouncy Castle's OpenPGP S2K, pymonocypher, application
password policies), none for argon2-cffi or the phc-winner-argon2 reference code. argon2-cffi 25.1.0
changes packaging metadata, adds Python 3.13/3.14 support, and makes `check_needs_rehash()` accept
bytes. argon2-cffi-bindings 26.1.0 changes only the build system and keeps the same vendored
commit `f57e61e`. No security fix in either.

### MedHub use and judgement

MedHub hashes and verifies passwords with a module-level `argon2.PasswordHasher()` (Argon2id,
library defaults), and verifies against a precomputed dummy hash for timing parity
(`app/auth/password.py`; SR-002, SR-025, SR-029; the RISK-005 design control "Argon2id hashing with
timing parity"). No published anomaly affects hashing, verification or constant-time comparison.
Not hazard-relevant; no RISK or PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 25.1.0 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): none found for 25.1.0 / argon2-cffi-bindings 25.1.0; nothing hazard-relevant. Record 1.0 → 1.1; approval record removed for re-review.
