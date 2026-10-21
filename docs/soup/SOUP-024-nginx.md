---
id: "SOUP-024"
type: soup
title: "nginx"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: "F5, Inc. / nginx authors"
soup_version: "alpine"
links: []
tags: ["soup", "layer:infrastructure", "class:B"]
---

# SOUP-024 — nginx alpine

> Floating `alpine` tag (PRB-001).

## Functional and performance requirements

TLS termination, HSTS and security headers at the reverse proxy (SR-001, SR-031), and static serving of the frontend bundle.

## Required hardware and software environment

`nginx:alpine` container image (reverse proxy and `frontend/Dockerfile` runtime stage); certificates in `infra/certs/`.

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
