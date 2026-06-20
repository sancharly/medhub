# NFR-005 Medical device regulatory compliance (MDR and FDA)

## Summary

The application shall comply with European (MDR) and United States (FDA) medical-device regulations applicable to medical device software.

## Description

MedHub, and in particular features such as the DICOM viewer that present clinical information for diagnostic or treatment purposes, fall under medical-device regulation. The product must be developed and documented so that it can demonstrate conformity with the EU Medical Device Regulation (MDR) and applicable US FDA requirements for software as a medical device. This is a system-wide constraint that drives documentation, traceability, risk management, and verification rigor for every requirement.

## Acceptance Criteria

1. Each requirement is documented, uniquely identified, version-controlled, and traceable, supporting a design-history and verification record.
2. Risk analysis is documented for each requirement (rationale, potential risks, control measures).
3. Clinical-information display features (e.g., DICOM viewer) have defined correctness acceptance criteria that are verified through system testing.
4. The development records (requirements, design, tests) form an auditable trail suitable for MDR/FDA technical documentation.

## Risk Analysis

### Rationale

Derived from the MedHub constraint "Medical device regulation": the application shall comply with EU and USA medical-device regulations (MDR and FDA).

### Potential Risks

- Compliance risk: failure to meet MDR/FDA requirements prevents lawful market placement.
- Safety risk: insufficient verification of clinical features could allow unsafe behavior to reach users.

### Control Measures

- Apply the documented requirements/risk/traceability process (this requirements set is part of it) and maintain it under version control.
- Verify clinical features through system testing with defined acceptance criteria; coordinate with NFR-006 (IEC 62304 process).

## Status

Approved

## Version History

Version 1.0 - Initial creation
