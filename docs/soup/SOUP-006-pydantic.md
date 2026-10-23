---
id: SOUP-006
type: soup
title: Pydantic
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-23"
manufacturer: Pydantic Services
soup_version: 2.13.4
anomaly_review: "2026-10-22"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-23"
approved_digest: 5f590d0bdfb0ec1efc244b82b15c739e83f5a59da8f43fadcd9b30798785e9a1
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-006 — Pydantic 2.13.4

## Functional and performance requirements

Request and response schema validation — the authoritative server-side validation behind SR-031.5 — and settings models.

## Required hardware and software environment

Python 3.12; pydantic-core (compiled).

Transitive dependencies covered by this record: pydantic-core.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for Pydantic 2.13.4 with pydantic-core 2.46.4, annotated-types 0.7.0, typing-inspection 0.4.2 and typing-extensions 4.15.0, the versions `backend/uv.lock` resolves. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database, https://github.com/pydantic/pydantic/security/advisories and https://github.com/pydantic/pydantic-core/security/advisories; NVD; https://github.com/pydantic/pydantic/releases

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `pydantic` 2.13.4, `pydantic-core` 2.46.4, `annotated-types` 0.7.0, `typing-inspection` 0.4.2, `typing-extensions` 4.15.0.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `pydantic@2.13.4`, `pydantic-core@2.46.4`.
- Repository advisories — https://github.com/pydantic/pydantic/security/advisories and https://github.com/pydantic/pydantic-core/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keyword `pydantic`.
- Release notes — https://github.com/pydantic/pydantic/releases/tag/v2.13.5 (2026-08-28), the only later patch in the 2.13 line.

### Findings

**None found** on 2026-10-22. No advisory in OSV, the GitHub Advisory Database or either repository.
All 43 recent NVD `pydantic` matches are for Pydantic AI, a different product. 2.13.5 fixes
validator reuse with plugins, missing GC traversal in pydantic-core (memory reclamation), and
smart-union field counting.

### MedHub use and judgement

Pydantic is the authoritative server-side validation behind SR-031.5 and the settings models.
MedHub uses no validation plugins, and its API schemas declare no unions of models (checked
2026-10-22), so the 2.13.5 fixes do not change its validation results. Not hazard-relevant; no
RISK or PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 2.13.4 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): none found for 2.13.4 / pydantic-core 2.46.4; nothing hazard-relevant. Record 1.0 → 1.1; approval record removed for re-review.
