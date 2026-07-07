---
id: "NFR-004"
type: nfr
title: "GDPR compliance"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links: []
tags: []
---

## Summary

The application shall comply with the GDPR in the storage and processing of personal and health data.

## Description

MedHub processes personal data and special-category health data of EU data subjects. The platform must satisfy GDPR principles and obligations: lawfulness and consent, data minimization, purpose limitation, data-subject rights (access, rectification, erasure, restriction), and protection of data at rest and in transit. This requirement applies system-wide and constrains data storage, access control, consent handling, and data export/deletion behavior across all features.

## Acceptance Criteria

1. Personal and health data are protected in transit and at rest using recognized encryption.
2. Patients can exercise core data-subject rights over their data: access (view) and control of consent for clinical-data sharing (grant/revoke).
3. Access to personal and health data follows data-minimization: each user type can access only the data necessary for its role.
4. The platform supports erasure/anonymization of a data subject's personal data on a lawful request.
5. Processing of personal data is recorded such that access can be audited.

## Risk Analysis

### Rationale

Derived from the MedHub constraint "GDPR": the application shall be compliant with GDPR laws in terms of data storage and treatment.

### Potential Risks

- Compliance risk: GDPR violations carry significant legal and financial penalties.
- Privacy risk: inadequate protection or over-broad access exposes special-category health data.

### Control Measures

- Encryption in transit and at rest, role-based access control with data minimization, consent management, audit logging, and an erasure mechanism are specified in software requirements.
- Data-protection design is reviewed against GDPR principles during design verification.
