---
id: RR-008
type: regulatory-requirement
title: Software of unknown provenance identification and monitoring
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 4b2e32b184d7522910a06563b1350f7e12b73e5efbfc52572f5bc841b79900a0
approval_note: self-approved
links: []
tags:
  - iec62304
  - regulatory
---

# RR-008 — Software of unknown provenance identification and monitoring

## Summary

Every third-party component must be uniquely identified and monitored for anomalies that could affect safety.

## Source

IEC 62304 §5.3.3, §5.3.4, §6.1 f, §7.1.2, §7.1.3, §8.1.2; FDA premarket cybersecurity guidance (software bill of materials); NFR-005, NFR-006.

## Obligation

The project shall maintain a SOUP list recording title, manufacturer and exact version of every third-party component, the functions and performance relied upon, the hardware and software it requires, and a dated review of its published anomaly list, and shall re-review on every change and before every release.

## Acceptance criteria

- Every dependency, runtime, container image and external service appears in the SOUP list with an exact version that matches the build.
- Each item records the anomaly source and the date it was reviewed.
- Hazard-relevant anomalies are escalated to risk records.

## Realized by

SOUP-001..SOUP-035 (one record per component). Problem reports: PRB-001, PRB-002, PRB-033. Task: TASK-154. Risk: RISK-010.
