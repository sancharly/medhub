---
id: "UN-002"
type: user-need
title: "Personal, authenticated user profile"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links: []
tags: []
---

## Summary

A user needs a personal, password-protected profile identified by their email address so that only they can access their account and associated information.

## Description

Every MedHub user (doctor, patient, administrative personnel, system administrator) handles or is associated with sensitive personal and health information. Users need to identify themselves uniquely and prove their identity before accessing the platform, and they need a profile that holds their personal information. The email address serves as the unique username. Without trustworthy identification, no access-control or data-protection guarantee can hold.

## Acceptance Criteria

1. A user can authenticate to the platform using an email address (username) and a password.
2. Each user has a profile containing their personal information that they can view.
3. Access to platform data and modules is only granted after successful authentication.
4. An email address uniquely identifies a single user account.

## Risk Analysis

### Rationale

Derived from the MedHub goal "User profiles": each user shall access their profile with a username (email) and a password. Authentication is the foundation of access control and data protection.

### Potential Risks

- Security risk: weak or absent authentication exposes personal and clinical data to unauthorized parties.
- Compliance risk: failure to control access conflicts with GDPR and medical-device cybersecurity expectations.

### Control Measures

- Email/password authentication and unique-account enforcement are specified in dedicated software requirements.
- Credential strength, session handling, and lockout are controlled by the cybersecurity NFR (NFR-007).
