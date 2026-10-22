---
id: SOUP-003
type: soup
title: Starlette
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Encode
soup_version: 1.3.1
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-003 — Starlette 1.3.1

## Functional and performance requirements

ASGI application and middleware chain; MedHub's security-headers and CSRF middleware subclass it directly (`app/core/security_middleware.py`).

## Required hardware and software environment

Python 3.12; anyio.

Transitive dependencies covered by this record: anyio.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for Starlette 1.3.1 and the anyio 4.14.0 this record covers (plus idna 3.18), the versions `backend/uv.lock` resolves. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database, https://github.com/Kludex/starlette/security/advisories and https://github.com/agronholm/anyio/security/advisories; NVD; https://github.com/Kludex/starlette/releases

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `starlette` 1.3.1, `anyio` 4.14.0, `idna` 3.18.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `starlette@1.3.1`, `anyio@4.14.0`.
- Repository advisories — https://github.com/Kludex/starlette/security/advisories and https://github.com/agronholm/anyio/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keyword `starlette`.
- Release notes — https://github.com/Kludex/starlette/releases/tag/1.3.1 (no later 1.3.x patch; 1.4.0 read for context).

### Findings

**Starlette 1.3.1: none found.** Every Starlette advisory published since 2025-10 is fixed at or
before 1.3.1: GHSA-82w8-qh3p-5jfq / CVE-2026-54283 (urlencoded `request.form()` limits ignored,
fixed in 1.3.1 itself, which is the content of the 1.3.1 release), GHSA-jp82-jpqv-5vv3 /
CVE-2026-54282 (1.3.0), GHSA-x746-7m8f-x49c / CVE-2026-48817 and GHSA-wqp7-x3pw-xc5r /
CVE-2026-48818 (1.1.0), GHSA-86qp-5c8j-p5mr / CVE-2026-48710 (1.0.1), GHSA-7f5h-v6xp-fcq8 /
CVE-2025-62727 (0.49.1). NVD lists the same CVEs.

**anyio 4.14.0: three advisories, all fixed in 4.14.2** (published 2026-07-07):

| ID | Summary | Affected | MedHub affected? |
|---|---|---|---|
| GHSA-3w57-8xmc-8v26 / CVE-2026-63349 (high) | `run_process` / `open_process` ignore `extra_groups` and can keep the parent's supplementary groups | 4.14.0–4.14.1 | No: neither MedHub nor Starlette starts subprocesses through anyio |
| GHSA-5p39-cfhj-2xmp / CVE-2026-64847 (moderate) | Process-pool workers can block on undrained stderr | < 4.14.2 | No: `anyio.to_process` is not used; Starlette only uses the thread pool |
| GHSA-82r6-8w77-94w6 / CVE-2026-63374 (critical) | `TLSStream` encodes host names with IDNA 2003, enabling certificate spoofing | < 4.14.2 | No: no runtime component opens an anyio TLS client stream; TLS is terminated by nginx (SOUP-024) |

`idna` 3.18: none found.

### MedHub use and judgement

MedHub's security-headers and CSRF middleware subclass Starlette (`app/core/security_middleware.py`,
RISK-005 CSRF control, SR-031) and the attachment upload uses Starlette's multipart form parsing
(SR-013). None of the Starlette advisories applies to 1.3.1. The anyio advisories apply to the
locked version but not to how MedHub runs it: no backend module imports anyio (checked
2026-10-22), and Starlette uses it only for its thread pool. Not hazard-relevant, no effect on
MedHub's behaviour: no RISK. Recorded for upgrade in [PRB-047](../problem-reports/PRB-047-runtime-transitives-with-published-advisories.md) (minor, 2026-10-22): raise anyio to
4.14.2 or later at the next dependency change, in a separate CR (CR-001 A-4 forbids upgrades
here).

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 1.3.1 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): Starlette none found; three anyio 4.14.0 advisories (fixed in 4.14.2) apply to the version but not to MedHub's use; nothing hazard-relevant; recorded for upgrade in PRB-047 (minor). Record 1.0 → 1.1; approval record removed for re-review.
