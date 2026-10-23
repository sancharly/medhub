---
id: SOUP-014
type: soup
title: Celery
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-23"
manufacturer: Celery project
soup_version: 5.6.3
anomaly_review: "2026-10-22"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-23"
approved_digest: 4bf8cda01887b5df902d591af247aa44e04ecf560dc7b6362ac37e44c64fe994
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-014 — Celery 5.6.3

## Functional and performance requirements

Asynchronous tasks with retry and backoff: activation and appointment notifications (SR-033, SR-035), session-revocation propagation (SR-034) and retention erasure (SR-024).

## Required hardware and software environment

Python 3.12; Redis server 7 as broker and result backend.

Transitive dependencies covered by this record: kombu 5.6.2, billiard 4.2.4, amqp 5.3.1.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for Celery 5.6.3 with kombu 5.6.2, billiard 4.2.4, amqp 5.3.1, vine 5.1.0, click 8.4.1, click-didyoumean 0.3.1, click-plugins 1.1.1.2, click-repl 0.3.0, prompt-toolkit 3.0.52, wcwidth 0.8.1, tzlocal 5.4.3, tzdata 2026.2 and python-dateutil 2.9.0.post0, the versions `backend/uv.lock` resolves. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database, https://github.com/celery/celery/security/advisories and https://github.com/celery/kombu/security/advisories; NVD; https://github.com/celery/celery/releases/tag/v5.6.3

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `celery` 5.6.3 and each transitive dependency at the version above.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `celery@5.6.3`, `kombu@5.6.2`.
- Repository advisories — https://github.com/celery/celery/security/advisories and https://github.com/celery/kombu/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keyword `celery`.
- Release notes — https://github.com/celery/celery/releases/tag/v5.6.3. 5.6.3 and kombu 5.6.2 are the latest releases (PyPI release history, `https://pypi.org/pypi/<package>/json`).

### Findings

**None found** on 2026-10-22. No advisory for Celery or any listed dependency in OSV, the GitHub
Advisory Database or the repositories. NVD's recent `celery` matches are other products that use
Celery (RELATE, Apache Airflow, Flower, BottleCRM, Open Zaak). 5.6.3's notes are bug fixes, among
them a worker that failed to reconnect after a Redis failover. There is no later release.

### MedHub use and judgement

MedHub runs asynchronous notification, session-revocation and retention-erasure tasks
(SR-033/034/035, SR-024; RISK-008 and RISK-007) on a Redis broker and result backend. It accepts
the JSON serializer only (`accept_content=["json"]`, `app/workers/celery_app.py`), so the classic
pickle-deserialization class of Celery issues does not apply. Not hazard-relevant; no RISK or PRB.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 5.6.3 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): none found for 5.6.3 or its transitive dependencies; nothing hazard-relevant. Record 1.0 → 1.1; approval record removed for re-review.
