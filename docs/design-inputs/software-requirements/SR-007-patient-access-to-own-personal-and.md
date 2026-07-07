---
id: "SR-007"
type: software-requirement
title: "Patient access to own personal and clinical data"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "UN-005"
    relation: derives_from
  - target: "NFR-004"
    relation: derives_from
tags: []
---

## Summary

The system shall allow a patient to view their own personal data and their own clinical data.

## Description

This requirement implements the patient's right to see their information. An authenticated patient can view their personal profile and their full clinical record (clinical entries and attachments) held in MedHub. The data shown is restricted to the patient's own records.

## Acceptance Criteria

1. An authenticated patient can view their own personal data.
2. An authenticated patient can view their own clinical entries and attached files.
3. A patient cannot view another patient's personal or clinical data.

## Origin Requirement

Derived from: User Need UN-005 "Patient ownership and control of their clinical data" and Non-Functional Requirement NFR-004 "GDPR compliance".

## Risk Analysis

### Rationale

Self-access to one's own records realizes patient autonomy and the GDPR right of access.

### Potential Risks

- Privacy risk: cross-patient data exposure breaches confidentiality.

### Control Measures

- Scope retrieval to the authenticated patient via the authorization mechanism (SR-005).
- Cover with tests including attempts to access other patients' data.
