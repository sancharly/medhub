---
id: "RR-010"
type: regulatory-requirement
title: "Medical device software general safety and performance"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["mdr", "fda", "regulatory"]
---

# RR-010 — Medical device software general safety and performance

## Summary

Software intended for a medical purpose must be developed and manufactured according to the state of the art, considering repeatability, reliability and performance for its intended use.

## Source

Regulation (EU) 2017/745 (MDR) Annex I §17.1-17.4 and §14.5; FDA 21 CFR Part 820.30 design controls; NFR-005.

## Obligation

The project shall define the intended use and the software safety class, verify the software against its requirements at unit, integration and system level, document residual anomalies at release, and keep the design history traceable and reproducible.

## Acceptance criteria

- The intended use and safety classification are recorded with their rationale.
- Verification exists at the three levels required for the safety class, with a test report per release.
- Known residual anomalies are listed and evaluated in the release's test report.
- The released build is reproducible from version-controlled sources.

## Realized by

SR-028, SR-026, SR-019. Records: ADD-002, the test plan and report records. Problem report: PRB-001.
