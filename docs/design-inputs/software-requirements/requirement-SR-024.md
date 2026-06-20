# SR-024 Personal data erasure

## Summary

The system shall support erasure or anonymization of a data subject's personal data upon a lawful request.

## Description

This requirement implements the GDPR right to erasure. On a lawful request, an authorized operator can remove or irreversibly anonymize a data subject's personal data, subject to any overriding legal retention obligations for clinical records. The operation is recorded for accountability.

## Acceptance Criteria

1. An authorized operator can initiate erasure or anonymization of a specified data subject's personal data.
2. After completion, the subject's personal identifying data is no longer retrievable through the application.
3. The erasure/anonymization action is recorded in the audit log with actor and timestamp.
4. Records subject to mandatory clinical retention are handled per a documented retention policy rather than silently deleted.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-004 "GDPR compliance".

## Risk Analysis

### Rationale

The right to erasure is a core GDPR data-subject right; the platform must be able to honor it.

### Potential Risks

- Compliance risk: inability to erase personal data violates GDPR.
- Safety/legal risk: erasing clinically/legally required records could breach retention law.

### Control Measures

- Provide an erasure/anonymization operation gated to authorized operators; reconcile with a documented retention policy; record in audit log (SR-023).
- Assumption: detailed retention policy is defined with regulatory/legal input post-MVP; MVP provides the technical capability and policy hook.

## Status

Approved

## Version History

Version 1.0 - Initial creation
