---
id: SOUP-033
type: soup
title: openapi-fetch
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: Drew Powers
soup_version: 0.17.0
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: b4a291448d630aea4b98964d15a75e20603fe8ea68006803b244988ccdbdc361
approval_note: self-approved
links: []
tags:
  - soup
  - layer:frontend
  - class:B
---

# SOUP-033 — openapi-fetch 0.17.0

## Functional and performance requirements

Typed HTTP client over the generated OpenAPI contract, with RFC 7807 error handling.

## Required hardware and software environment

Browser `fetch`; the generated `openapi.ts` types.

## Anomaly list review

**Not yet performed.** No published anomaly list, release notes or advisory database has been
reviewed for this exact version, so `anomaly_review` is absent. The first review is TASK-154; until
it lands this item fails the release gate's SOUP check.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
