---
id: SOUP-003
type: soup
title: Starlette
status: in_review
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-29"
manufacturer: Encode
soup_version: 1.3.1
anomaly_review: "2026-10-29"
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

Python 3.12; anyio 4.14.2.

Transitive dependencies covered by this record, at the versions locked in `backend/uv.lock`: anyio 4.14.2 (with idna 3.18 and typing-extensions 4.15.0, which anyio requires and which the 4.14.0 → 4.14.2 lock change left unchanged, TASK-164). Starlette's task groups, memory streams and thread-pool limiter (`CapacityLimiter`) run on anyio.

## Anomaly list review

**Reviewed 2026-10-29** (TASK-164, CR-003 AC-14) for Starlette 1.3.1 and the anyio 4.14.2 this record covers (plus idna 3.18), the versions `backend/uv.lock` resolves. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database, https://github.com/Kludex/starlette/security/advisories and https://github.com/agronholm/anyio/security/advisories; NVD; https://anyio.readthedocs.io/en/stable/versionhistory.html; https://github.com/Kludex/starlette/releases

### Sources checked

Same sources as the 2026-10-22 review, read on 2026-10-29:

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `starlette` 1.3.1, `anyio` 4.14.2 and `idna` 3.18 each returned no vulnerability. The same query for `anyio` 4.14.0 returned GHSA-3w57-8xmc-8v26, GHSA-5p39-cfhj-2xmp and GHSA-82r6-8w77-94w6 (with their PYSEC aliases), which confirms that the query works and that those advisories no longer apply.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `starlette@1.3.1` and `anyio@4.14.2` returned no advisory. `anyio@4.14.0` returned the same three.
- Repository advisories — https://github.com/Kludex/starlette/security/advisories and https://github.com/agronholm/anyio/security/advisories (published advisories listed through the REST API). The anyio repository lists exactly three, all published 2026-07-07 and all with patched version 4.14.2. The newest Starlette advisories are fixed at or before 1.3.1 (GHSA-82w8-qh3p-5jfq at 1.3.1, published 2026-06-12), and none has been published since.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keywords `starlette` and `anyio`. The Starlette entries are the CVEs of the 2026-10-22 review, and the other new entries are other products (starlette-admin, NiceGUI, Pipecat, LiteLLM, vLLM and similar). For anyio, the keyword search returns the three CVEs below (CVE-2026-63349: "Awaiting Analysis", CVSS 4.0 score 7.0) and CVE-2026-107286, which is Pydantic AI's concurrency-slot defect in its own code, not an anyio defect.
- Version history — https://anyio.readthedocs.io/en/stable/versionhistory.html, entries 4.14.1 and 4.14.2. PyPI lists 4.14.2 (https://pypi.org/project/anyio/4.14.2/) and a later 4.15.1 (uploaded 2026-09-05). The lock deliberately stays on 4.14.2, the smallest move that fixes the PRB-047 advisories (CR-003 D-3).
- Release notes — https://github.com/Kludex/starlette/releases/tag/1.3.1 (unchanged since the previous review; no later 1.3.x patch).

### Findings

**Starlette 1.3.1: none found.** Every Starlette advisory published since 2025-10 is fixed at or
before 1.3.1: GHSA-82w8-qh3p-5jfq / CVE-2026-54283 (urlencoded `request.form()` limits ignored,
fixed in 1.3.1 itself), GHSA-jp82-jpqv-5vv3 / CVE-2026-54282 (1.3.0), GHSA-x746-7m8f-x49c /
CVE-2026-48817 and GHSA-wqp7-x3pw-xc5r / CVE-2026-48818 (1.1.0), GHSA-86qp-5c8j-p5mr /
CVE-2026-48710 (1.0.1), GHSA-7f5h-v6xp-fcq8 / CVE-2025-62727 (0.49.1). NVD lists the same CVEs.

**anyio 4.14.2 and idna 3.18: none found.** The three advisories of the 2026-10-22 review
(PRB-047) are **fixed at 4.14.2**, and the 4.14.2 version history confirms each fix:

| ID | Summary | Affected | Status at 4.14.2 |
|---|---|---|---|
| GHSA-3w57-8xmc-8v26 / CVE-2026-63349 | `run_process` / `open_process` ignore `extra_groups` and can keep the parent's supplementary groups | 4.14.0–4.14.1 | **Fixed in 4.14.2** ("Fixed `anyio.open_process()` (and `run_process()`) ignoring the `extra_groups` argument") |
| GHSA-5p39-cfhj-2xmp / CVE-2026-64847 | Process-pool workers can block on undrained stderr | < 4.14.2 | **Fixed in 4.14.2** ("Fixed `to_process.run_sync()` deadlocking when the worker function writes enough data to `sys.stderr`") |
| GHSA-82r6-8w77-94w6 / CVE-2026-63374 | `TLSStream` encodes host names with IDNA 2003, enabling certificate spoofing | < 4.14.2 | **Fixed in 4.14.2** ("Fixed `TLSStream.wrap()` matching an internationalized host name ... using IDNA 2003 instead of IDNA 2008") |

**Changes 4.14.0 → 4.14.2 (version history).** 4.14.1: pytest-plugin fixture teardown on
asyncio, `CapacityLimiter.total_tokens` accepting 0 outside an event loop, `Process.wait()` on
asyncio, and a `Process.aclose()` deadlock on asyncio (subprocess blocked on a full stdout or
stderr pipe). 4.14.2: the three security fixes above, `ByteReceiveStream.receive()` argument
validation, `CapacityLimiter.total_tokens` accepting infinity, `acquire_nowait()` raising
`anyio.WouldBlock` on the trio backend, `CapacityLimiter` on asyncio no longer over-granting
tokens, and "unnecessary CPU spin when delivering cancellation from `CancelScope` on asyncio under
certain conditions, including improper cancel scope nesting". Two of these touch paths MedHub
reaches through Starlette: the `CapacityLimiter` fix (its thread pool) and the `CancelScope`
fix (`BaseHTTPMiddleware` calls `task_group.cancel_scope.cancel()`,
`starlette/middleware/base.py:121` in the locked 1.3.1, and both MedHub security middlewares
subclass it). The process, TLS, stream-validation and trio entries are not reached. No entry
changes how task groups or memory streams deliver or order data.

### MedHub use and judgement

MedHub's security-headers and CSRF middleware subclass Starlette (`app/core/security_middleware.py`,
RISK-005 CSRF control, SR-031) and the attachment upload uses Starlette's multipart form parsing
(SR-013). None of the Starlette advisories applies to 1.3.1, and no anyio advisory applies to
4.14.2. No backend module imports anyio (checked 2026-10-29), and Starlette uses it for task
groups, memory streams and its thread pool. Not hazard-relevant, MedHub not affected: no RISK, no
PRB. PRB-047 is resolved for this item.

**Upgrade impact (§7.4).** The behaviour that matters is the middleware path of the RISK-005
control. Two changes touch a path MedHub uses. The `CapacityLimiter` fix: Starlette's thread pool
uses that limiter, so its limit is now honoured exactly. The `CancelScope` fix: it removes a CPU
spin when a cancellation is delivered on asyncio, which `BaseHTTPMiddleware` triggers through
`task_group.cancel_scope.cancel()`. Both are corrections in the safe direction (the second
affects CPU use only, not what is delivered). A regression in task groups or streams would show as failed requests or missing
headers, which the TS-011 header and CSRF tests would catch. The full backend suite passes on
4.14.2 (499 tests), and the security headers and CSRF enforcement were exercised over the
rebuilt stack (`infra/smoke-test.sh` 17/17; login, an authenticated mutation with its CSRF token,
and logout through the proxy, TASK-164).

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 1.3.1 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): Starlette none found; three anyio 4.14.0 advisories (fixed in 4.14.2) apply to the version but not to MedHub's use; nothing hazard-relevant; recorded for upgrade in PRB-047 (minor). Record 1.0 → 1.1; approval record removed for re-review.
- 2026-10-29 — anyio 4.14.0 → 4.14.2 (transitive); Starlette 1.3.1 unchanged; PRB-047, CR-003 (D-3), TASK-164. Second anomaly-list review, at the new version: no anomaly applies, and the three anyio advisories are fixed at 4.14.2. The lock moved only anyio (and urllib3, SOUP-019); idna 3.18 and typing-extensions 4.15.0 unchanged. Change analysis: two fixes touch a path MedHub uses, the `CapacityLimiter` fix (thread pool) and the `CancelScope` cancellation CPU-spin fix (`BaseHTTPMiddleware`), both in the safe direction (the second is CPU-only); the middleware tests and the rebuilt stack confirm the RISK-005 controls. Record 1.1 → 1.2; approval record removed for re-review.
