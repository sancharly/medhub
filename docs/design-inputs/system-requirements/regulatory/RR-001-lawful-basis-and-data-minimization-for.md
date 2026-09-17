---
id: "RR-001"
type: regulatory-requirement
title: "Lawful basis and data minimization for processing health data"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links:
  - target: "UN-005"
    relation: derives_from
tags: ["gdpr", "privacy"]
---

# RR-001 — Lawful basis and data minimization for processing health data

## Summary

Personal and clinical data may only be processed for the care purpose the patient's data was collected for, and every actor may see only the data that purpose requires.

## Source

Regulation (EU) 2016/679 (GDPR) Art. 5(1)(a) lawfulness and Art. 5(1)(c) data minimization; NFR-004.

## Obligation

The software shall restrict every read and write of personal or clinical data to the minimum set required by the actor's role and the patient's consent, and shall not expose fields beyond that set.

## Acceptance criteria

- Every endpoint returning personal data applies a role projection; administrative personnel never receive clinical data.
- Access without a role right and a consent basis is refused.
- A field-level review exists for each response schema showing why each field is needed.

## Realized by

SR-005, SR-006, SR-007, SR-008, SR-009, SR-036. Risk: RISK-001.
