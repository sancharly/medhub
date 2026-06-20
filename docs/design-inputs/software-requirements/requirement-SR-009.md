# SR-009 Administrative personnel non-clinical data scope

## Summary

The system shall allow administrative personnel to view only a limited set of non-clinical personal fields of patients and doctors and shall deny them access to any clinical data.

## Description

This requirement implements the administrative-personnel restriction. Administrative staff can read a limited set of non-clinical fields (at minimum name, family name, date of birth) of patients and doctors to perform their duties, and the system blocks any access by them to clinical data (clinical entries, attachments, imaging).

## Acceptance Criteria

1. Administrative personnel can view at least the name, family name, and date of birth of patients and doctors.
2. Administrative personnel cannot retrieve clinical entries, attachments, or any clinical data.
3. Any request by administrative personnel for clinical data is denied by the authorization mechanism.

## Origin Requirement

Derived from: User Need UN-006 "Administrative personnel limited access and scheduling" and Non-Functional Requirement NFR-004 "GDPR compliance".

## Risk Analysis

### Rationale

Least-privilege access for administrative staff enforces confidentiality and GDPR data-minimization while enabling their operational tasks.

### Potential Risks

- Privacy risk: leakage of clinical data to non-clinical staff breaches confidentiality.

### Control Measures

- Define a non-clinical field projection for administrative personnel; deny clinical-data operations via SR-005.
- Cover with automated tests asserting clinical-data access is blocked.

## Status

Approved

## Version History

Version 1.0 - Initial creation
