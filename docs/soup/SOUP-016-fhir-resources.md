---
id: SOUP-016
type: soup
title: fhir.resources
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Md Nazrul Islam (nazrulworld)
soup_version: 8.2.0
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-016 — fhir.resources 8.2.0

## Functional and performance requirements

FHIR R4 resource models that the clinical data model is aligned with (SR-021).

## Required hardware and software environment

Python 3.12; fhir-core 1.1.8; Pydantic (SOUP-006).

Transitive dependencies covered by this record: fhir-core 1.1.8.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for fhir.resources 8.2.0 with fhir-core 1.1.8, the versions `backend/uv.lock` resolves. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database, https://github.com/nazrulworld/fhir.resources/security/advisories and https://github.com/nazrulworld/fhir-core/security/advisories; NVD; https://pypi.org/project/fhir.resources/; https://pypi.org/project/fhir-core/

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `fhir.resources` 8.2.0, `fhir-core` 1.1.8.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `fhir.resources@8.2.0`, `fhir-core@1.1.8`.
- Repository advisories — https://github.com/nazrulworld/fhir.resources/security/advisories and https://github.com/nazrulworld/fhir-core/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keyword `fhir.resources`.
- Changelogs — https://pypi.org/project/fhir.resources/ (8.2.0; 8.3.0 of 2026-07-03 is the next release, no 8.2.x patch) and https://pypi.org/project/fhir-core/ (1.1.8 and the later patches 1.1.9–1.1.12, 2026-06-28 to 2026-10-18).

### Findings

**No security advisory** on 2026-10-22, in OSV, GitHub or NVD. The later fhir-core patches fix
validation-correctness bugs that apply to 1.1.8: a Decimal input losing its exponent (1.1.9);
`None` accepted in lists of complex types, and negative values accepted for
`unsignedInt`/`positiveInt` (1.1.11); leap seconds rejected (1.1.12). fhir.resources 8.3.0 makes
`Extension.url` required.

### MedHub use and judgement

The clinical data model is aligned with FHIR R4 (SR-021). No backend module imports
fhir.resources at runtime: it is used only by `backend/tests/db/test_fhir_mapping.py` (checked
2026-10-22), and stored FHIR extensions are plain JSONB. The fhir-core validation bugs therefore
cannot change what MedHub stores or returns. They matter only if the models are used to validate
data at runtime later, which would be a change to analyse then. Not hazard-relevant (RISK-002
unaffected); no RISK or PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 8.2.0 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): none found for 8.2.0 / fhir-core 1.1.8 security-wise; later fhir-core validation fixes noted; not imported at runtime; nothing hazard-relevant. Record 1.0 → 1.1; approval record removed for re-review.
