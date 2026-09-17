---
id: "RR-003"
type: regulatory-requirement
title: "Security of processing: encryption and access control"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links:
  - target: "UN-005"
    relation: derives_from
tags: ["gdpr", "security"]
---

# RR-003 — Security of processing: encryption and access control

## Summary

Personal and health data must be protected by state-of-the-art technical measures appropriate to the risk.

## Source

GDPR Art. 32(1)(a)-(b); IEC 62304 §5.2.2 e; NFR-004, NFR-007.

## Obligation

The software shall encrypt personal and clinical data in transit and at rest, authenticate every request, enforce authorization on every protected operation, and manage session and credential material so that its compromise does not expose stored data.

## Acceptance criteria

- TLS 1.2+ for all traffic; HSTS enabled at the proxy.
- Clinical fields encrypted at rest with an authenticated cipher and a documented key lifecycle.
- Passwords stored with a memory-hard KDF; sessions opaque, expiring and revocable.

## Realized by

SR-001, SR-002, SR-022, SR-025, SR-029, SR-030, SR-031. Risks: RISK-005, RISK-011.
