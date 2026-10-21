---
id: "RR-007"
type: regulatory-requirement
title: "Risk management for medical device software"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
links: []
tags: ["iso14971", "iec62304", "regulatory"]
---

# RR-007 — Risk management for medical device software

## Summary

A risk management process must identify hazards the software can contribute to, control them, and verify the controls, throughout the lifecycle.

## Source

ISO 14971:2019 §4.4, §5-8; IEC 62304 §7.1-7.4; NFR-005, NFR-006.

## Obligation

The project shall maintain a risk management file: a plan defining severity, probability and acceptability criteria, a risk record per hazardous situation with its control measures and their verification, an evaluation of residual risk accepted by a competent human, and a risk analysis of every change.

## Acceptance criteria

- A risk management plan record exists with scales and acceptability criteria approved by the owner.
- Every safety-relevant software requirement traces to a risk record via `mitigates`.
- Every risk control names the verification record that proves it works.
- Residual risk acceptance is recorded with the decider and date.

## Realized by

PLAN-005, the `risk_matrix` in `docs/medtrace.yml`, RISK-001..RISK-011. Task: TASK-147.
