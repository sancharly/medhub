# SR-022 Encryption in transit and at rest

## Summary

The system shall encrypt all data in transit using TLS and encrypt personal and health data at rest.

## Description

This requirement implements the encryption obligations shared by GDPR and cybersecurity. All client-server communication uses TLS. Personal and health data, including clinical entries and file attachments such as DICOM images, are encrypted at rest in storage. Encryption uses recognized, current algorithms and key management.

## Acceptance Criteria

1. All client-server traffic is transmitted over TLS; non-TLS access is not served.
2. Personal and health data, including clinical entries and attachments, are encrypted at rest using a recognized algorithm (e.g., AES-256).
3. Encryption keys are managed so that data is not recoverable without authorized key access.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-004 "GDPR compliance" and NFR-007 "Cybersecurity".

## Risk Analysis

### Rationale

Encryption protects special-category health data and is required by GDPR and medical-device cybersecurity guidance.

### Potential Risks

- Security/compliance risk: unencrypted data in transit or at rest exposes health data and violates regulation.

### Control Measures

- Enforce TLS (SR-001) and storage-level encryption; verify configuration during security review and system testing.

## Status

Approved

## Version History

Version 1.0 - Initial creation
