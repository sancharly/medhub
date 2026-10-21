---
id: RR-002
type: regulatory-requirement
title: Right to erasure of personal data
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 07f751893211c0b8972e6ce485243d9e063964ac440674852f0d897d9881b134
approval_note: self-approved
links:
  - target: UN-005
    relation: derives_from
tags:
  - gdpr
  - privacy
---

# RR-002 — Right to erasure of personal data

## Summary

A data subject can obtain erasure of their personal data, while clinical information that must be retained is kept in a form that is no longer attributable to them.

## Source

GDPR Art. 17 (right to erasure) with Art. 17(3)(c)/(h) exceptions; NFR-004; ADR-0013.

## Obligation

The software shall, on an authorized deletion request, remove or irreversibly anonymize the data subject's identifying data, retain the anonymized clinical dataset only for the declared retention period, and permanently erase it afterwards.

## Acceptance criteria

- Deletion anonymizes rather than silently dropping clinical data, and re-keys it to the anonymized dataset.
- The retention deadline is recorded per dataset and enforced by a scheduled erasure.
- The data subject receives a retrieval code whose salted hash only is stored.

## Realized by

SR-024, SR-034. Tasks: TASK-035, TASK-036, TASK-116. Risk: RISK-008.
