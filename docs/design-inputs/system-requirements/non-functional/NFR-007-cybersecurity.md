---
id: "NFR-007"
type: nfr
title: "Cybersecurity"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links: []
tags: []
---

## Summary

The application shall comply with cybersecurity standards and guidance applicable to medical device software in Europe and the USA, protecting confidentiality, integrity, and availability of data.

## Description

As a medical device handling sensitive health data, MedHub must implement security controls consistent with recognized medical-device cybersecurity guidance (e.g., FDA pre-market cybersecurity guidance and EU MDR/IMDRF expectations). This applies system-wide and covers secure authentication and session management, transport and storage encryption, protection against common web vulnerabilities, audit logging of security-relevant events, and resilience against unauthorized access. It complements GDPR (NFR-004) and the medical-device regulation (NFR-005).

## Acceptance Criteria

1. All data is transmitted over encrypted channels (TLS) and sensitive data is encrypted at rest.
2. Authentication enforces credential strength and protects against brute force (e.g., password complexity and account lockout after repeated failed attempts).
3. Sessions expire after a defined period of inactivity and can be invalidated.
4. The application mitigates common web vulnerabilities (e.g., injection, broken access control, cross-site scripting) following recognized guidance such as OWASP.
5. Security-relevant events (authentication, access to clinical data, consent changes, administrative actions) are recorded in an audit log.

## Risk Analysis

### Rationale

Derived from the MedHub constraint "Cyber security": the application shall comply with cybersecurity standards and guidance applicable to medical device software in Europe and the USA.

### Potential Risks

- Security risk: breaches could expose special-category health data and compromise patient safety.
- Compliance risk: insufficient cybersecurity violates MDR/FDA and GDPR expectations.
- Availability risk: attacks could render clinical workflows unavailable.

### Control Measures

- Specify and verify authentication hardening, encryption, session management, vulnerability mitigation, and audit logging in software requirements traced to this NFR.
- Conduct security review of changes (per the development plan's code review activity) before integration.
