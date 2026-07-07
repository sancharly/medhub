---
id: "NFR-006"
type: nfr
title: "IEC 62304 development process compliance"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links: []
tags: []
---

## Summary

The application shall be developed in accordance with the IEC 62304 standard for medical device software lifecycle processes.

## Description

IEC 62304 defines the lifecycle processes for medical device software, including requirements analysis, architectural design, implementation, integration, and testing, each with controlled records. MedHub's development must follow these processes as defined in the project's software development plan, producing the corresponding controlled artifacts and traceability. This requirement constrains how the product is built and documented rather than a runtime behavior, and applies across the whole project.

## Acceptance Criteria

1. The development follows the lifecycle activities defined in the software development plan (requirements analysis, architecture design, implementation, code review, integration, testing).
2. Each lifecycle activity produces its defined, version-controlled outputs.
3. Requirements are traceable from user needs and non-functional requirements through software requirements to architecture and to tests.
4. All software requirements are traced to at least one system test before release.

## Risk Analysis

### Rationale

Derived from the MedHub constraint "IEC 62304": the application shall be developed in accordance with IEC 62304.

### Potential Risks

- Compliance risk: a non-conforming process undermines the regulatory submission and product certification.
- Quality/safety risk: skipping lifecycle controls increases the chance of undetected defects reaching production.

### Control Measures

- Follow the software development plan's activities and record outputs under version control.
- Maintain bidirectional traceability (origin-requirement links in software requirements) and trace requirements to tests during the testing phase.
