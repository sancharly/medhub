---
id: "NFR-002"
type: nfr
title: "FHIR data governance"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links: []
tags: []
---

## Summary

Clinical and personal health data governance shall comply with the FHIR standard to enable standardization and future interoperability.

## Description

To support future interoperability with other healthcare systems and to standardize how health data is structured, MedHub's data governance for personal and clinical information shall follow the FHIR (Fast Healthcare Interoperability Resources) standard. This applies to how core clinical and demographic entities (such as patients, practitioners, appointments, and clinical/observation records) are modeled and exchanged. For the MVP this means the data model for these entities aligns with the corresponding FHIR resources.

## Acceptance Criteria

1. Core domain entities (patient, practitioner/doctor, appointment, clinical entry/observation) are modeled in alignment with their corresponding FHIR resource definitions.
2. The field structure of these entities is traceable to FHIR resource fields.
3. The data representation is documented so that future FHIR-based exchange (export/import) can be implemented without redesigning the model.

## Risk Analysis

### Rationale

Derived from the MedHub constraint "FHIR standard": data governance shall comply with FHIR for standardization and future interoperability.

### Potential Risks

- Interoperability risk: a non-standard model would make future integration with external systems costly or infeasible.
- Compliance risk: divergence from recognized healthcare standards weakens regulatory and clinical acceptance.

### Control Measures

- Map MVP domain entities to FHIR resources during architecture design and document the mapping.
- Review the data model against FHIR resource definitions as part of design verification.
