# SR-021 FHIR-aligned data model

## Summary

The system shall model its core domain entities (patient, doctor/practitioner, appointment, clinical entry) in alignment with the corresponding FHIR resources.

## Description

This requirement implements FHIR data governance. The data structures for patients, practitioners, appointments, and clinical entries (observations/clinical records) are designed to align field-by-field with their corresponding FHIR resource definitions, and the mapping is documented so future FHIR-based export/import can be added without redesigning the model.

## Acceptance Criteria

1. Patient, practitioner/doctor, appointment, and clinical-entry entities map to their corresponding FHIR resources.
2. A documented mapping exists between each entity's fields and the FHIR resource fields.
3. The model is reviewed against FHIR resource definitions and the review is recorded.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-002 "FHIR data governance".

## Risk Analysis

### Rationale

FHIR alignment enables future interoperability and standardizes the health-data model, a recognized healthcare expectation.

### Potential Risks

- Interoperability risk: a non-standard model makes future integration costly or infeasible.

### Control Measures

- Map entities to FHIR resources during architecture design; review the model against FHIR definitions as part of design verification.

## Status

Approved

## Version History

Version 1.0 - Initial creation
