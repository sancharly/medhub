---
id: SOUP-002
type: soup
title: FastAPI
status: approved
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-11-13"
manufacturer: Sebastián Ramírez (tiangolo)
soup_version: 0.138.0
anomaly_review: "2026-10-22"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-13"
approved_digest: 3b1121df3a516bfccfaee624dabf07b4169a3548a4ee8c329f3ab0cbb276dabd
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-002 — FastAPI 0.138.0

## Functional and performance requirements

HTTP routing, dependency injection used as the authorization enforcement point on every protected route (SR-005), request validation through Pydantic, and OpenAPI 3.1 generation.

Relied-on behaviour (CR-006, TASK-227, ADR-0023): a dependency declared with
`Depends(..., scope="function")` (`fastapi/params.py:749`) is torn down on the function exit stack,
after the endpoint has returned and its response has been serialised and before the response is sent
(`fastapi/routing.py`); an exception raised there reaches the exception handlers, so a failed commit
is a 5xx response. The dependency cache key includes the scope (`fastapi/dependencies/models.py`), so
mixing scopes for one dependency gives two instances in one request. MedHub declares `get_db` only
through one `scope="function"` alias and a test enforces it. FastAPI 0.138 keeps included routers lazy:
the scope test reads routes with `fastapi.routing.iter_route_contexts`.

## Required hardware and software environment

Python 3.12; Starlette (SOUP-003); Pydantic (SOUP-006).

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for FastAPI 0.138.0, the version `backend/uv.lock` resolves, with annotated-doc 0.0.4. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database and https://github.com/fastapi/fastapi/security/advisories; NVD; https://github.com/fastapi/fastapi/releases

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `fastapi` 0.138.0, `annotated-doc` 0.0.4.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `fastapi@0.138.0`.
- FastAPI repository advisories — https://github.com/fastapi/fastapi/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keyword `fastapi`.
- Release notes — https://github.com/fastapi/fastapi/releases/tag/0.138.0 and the later patches in the 0.138 line, 0.138.1 (2026-06-25) and 0.138.2 (2026-06-29).

### Findings

**None found** on 2026-10-22. OSV and the GitHub Advisory Database return no advisory for
`fastapi` 0.138.0 or `annotated-doc` 0.0.4, and the repository has no published advisory. NVD's
57 `fastapi` matches are all for third-party projects built on FastAPI (for example fastapi-guard,
FastAPI Users, fastapi-sso), none for FastAPI itself. 0.138.1 and 0.138.2 contain refactors and CI
changes only; 0.138.2 changes `app.frontend()`, which MedHub does not call.

### MedHub use and judgement

MedHub relies on FastAPI's routing and dependency injection as the authorization enforcement
point (SR-005, RISK-001) and on its Pydantic request validation. No published anomaly touches either.
Not hazard-relevant; no RISK or PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 0.138.0 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): none found for 0.138.0; nothing hazard-relevant. Record 1.0 → 1.1; approval record removed for re-review.
- 2026-11-13 — 0.138.0 (unchanged). Relied-on behaviour added: `Depends(scope="function")` teardown before the response (TASK-227, CR-006). Record 1.1 → 1.2; approval record removed for re-review. The anomaly review of 2026-10-22 is unchanged.
