---
id: SOUP-007
type: soup
title: pydantic-settings
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-23"
manufacturer: Pydantic Services
soup_version: 2.14.2
anomaly_review: "2026-10-22"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-23"
approved_digest: 8fae657afa678be50c88c6239809f4acf335cd4ec09f011407a1271a980390bd
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-007 — pydantic-settings 2.14.2

## Functional and performance requirements

Typed 12-factor configuration and secret handling (`SecretStr`) for every backend item (NFR-007).

## Required hardware and software environment

Python 3.12; Pydantic (SOUP-006); environment variables injected at deploy time.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for pydantic-settings 2.14.2 with python-dotenv 1.2.2, the versions `backend/uv.lock` resolves. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database and https://github.com/pydantic/pydantic-settings/security/advisories; https://github.com/pydantic/pydantic-settings/releases

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `pydantic-settings` 2.14.2, `python-dotenv` 1.2.2.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `pydantic-settings@2.14.2`.
- Repository advisories — https://github.com/pydantic/pydantic-settings/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keyword `pydantic` (covers pydantic-settings).
- Release notes — https://github.com/pydantic/pydantic-settings/releases (no later 2.14.x patch; 2.15.0 read for context).

### Findings

**None found** for 2.14.2 on 2026-10-22. The one repository advisory, GHSA-4xgf-cpjx-pc3j
(`NestedSecretsSettingsSource` follows symlinks outside `secrets_dir`; affected 2.12.0 to before
2.14.2), is fixed in 2.14.2 itself. `python-dotenv` 1.2.2: none found.

### MedHub use and judgement

MedHub's `Settings` (`app/core/config.py`) reads environment variables into `SecretStr` fields and
uses no `secrets_dir`. Not hazard-relevant; no RISK or PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 2.14.2 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): none found for 2.14.2 (GHSA-4xgf-cpjx-pc3j is fixed in this version); nothing hazard-relevant. Record 1.0 → 1.1; approval record removed for re-review.
