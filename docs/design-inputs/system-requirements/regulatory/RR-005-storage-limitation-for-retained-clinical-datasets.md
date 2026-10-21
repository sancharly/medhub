---
id: RR-005
type: regulatory-requirement
title: Storage limitation for retained clinical datasets
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: a0ee4f72c0c666ed52731d984e209bae8f0bd33c469942fe15cd6c3e09302a77
approval_note: self-approved
links:
  - target: UN-005
    relation: derives_from
tags:
  - gdpr
  - privacy
---

# RR-005 — Storage limitation for retained clinical datasets

## Summary

Data must not be kept in identifiable or retrievable form longer than the purpose requires.

## Source

GDPR Art. 5(1)(e) storage limitation; ADR-0013; NFR-004.

## Obligation

The software shall hold anonymized clinical datasets for the declared retention period of five years from the deletion request and shall permanently erase them once the deadline passes, without manual intervention.

## Acceptance criteria

- Each anonymized dataset carries a retention deadline.
- A scheduled job erases datasets past their deadline and records the erasure.
- Retrieval with the anonymization code is refused after the deadline.

## Realized by

SR-024. Tasks: TASK-036, TASK-121, TASK-141. Risk: RISK-008.
