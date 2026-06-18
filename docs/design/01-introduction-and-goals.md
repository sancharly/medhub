# 01 - Introduction and Goals

## Purpose

MedHub is a regulated medical web application that acts as a central hub for Protected Health Information (PHI) and clinical activity. It centralizes patient personal and clinical data, lets doctors record clinical entries with attached files (including DICOM imaging), lets patients own and control access to their data, lets administrative personnel schedule appointments, and lets a system administrator provision functionality through a modular **plugin** architecture. The first plugin is a **DICOM viewer** that demonstrates the module mechanism. The architecture must satisfy GDPR, EU MDR, US FDA, IEC 62304 and recognized medical-device cybersecurity expectations.

## Requirements Overview

High-level requirements driving the architecture (full set in `docs/design-inputs/`; full mapping in [traceability-matrix.md](traceability-matrix.md)).

| ID                                    | Requirement                            | Description                                                        | Priority |
|---------------------------------------|----------------------------------------|--------------------------------------------------------------------|----------|
| UN-001 / SR-001                       | Browser-based access                   | Web app over HTTPS, no client install                              | High     |
| UN-002/003 / SR-002–005               | Authenticated, differentiated access   | Email/password auth; 4 user types; deny-by-default RBAC            | High     |
| UN-004/005 / SR-006–008               | Doctor/patient data scoping & consent  | Doctor sees own patients; patient grants/revokes; immediate effect | High     |
| UN-006/007/013 / SR-009–011, 035, 036 | Appointments & consent-on-confirmation | Admin scheduling; patient confirm grants per-appointment consent   | High     |
| UN-008 / SR-012, 013                  | Clinical entries + attachments         | Doctor records entries; attach DICOM/reports                       | High     |
| UN-009/010 / SR-014–016               | Groups & plugin modules                | Sysadmin groups; per-group module enablement; extensibility        | High     |
| UN-011 / SR-017, 018                  | DICOM viewer                           | Open CT/MRI/X-ray; window/level, zoom, pan, slice nav              | High     |
| UN-012 / SR-032–034                   | Account lifecycle                      | Role-constrained creation, email activation, deactivate/delete     | High     |
| NFR-001/003/009 / SR-019, 020, 027    | Cross-browser, responsive, usable      | Safari/Firefox/Chrome/Edge; phone/tablet/desktop; minimal training | High     |
| NFR-002 / SR-021                      | FHIR data governance                   | FHIR R4-aligned model, documented mapping                          | Medium   |
| NFR-004/007 / SR-022–025, 029–031     | GDPR & cybersecurity                   | Encryption, audit, erasure, password/lockout/session, OWASP        | High     |
| NFR-005/006 / SR-028                  | MDR/FDA & IEC 62304                    | Traceable, version-controlled, verifiable records                  | High     |
| NFR-008 / SR-026                      | Performance                            | Routine ops <3s; DICOM initial render <10s                         | Medium   |

## Quality Goals

The top quality goals (highest priority for stakeholders), in order:

| Priority | Quality Goal                             | Description                                                                                                                                                                                               |
|----------|------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1        | **Security & Privacy (Confidentiality)** | PHI is protected by deny-by-default access control, encryption in transit/at rest, consent enforcement, and audit. Broken access control or data leakage is the worst outcome (NFR-004, NFR-007, SR-005). |
| 2        | **Safety / Correctness**                 | Clinical information — especially DICOM rendering and consent state — is correct and well-attributed; incorrect display or wrong grant evaluation could cause clinical error (NFR-005, SR-017, SR-036).   |
| 3        | **Compliance & Traceability**            | The design is documented, version-controlled, and traceable from user needs to tests, suitable for MDR/FDA/IEC 62304 audit (NFR-005, NFR-006, SR-028).                                                    |
| 4        | **Extensibility**                        | New modules are added without modifying existing ones, enabled per group (SR-015, SR-016).                                                                                                                |
| 5        | **Usability & Reach**                    | Works across the four major browsers and phone/tablet/desktop with minimal training (NFR-001, NFR-003, NFR-009).                                                                                          |

## Stakeholders

| Role                             | Expectations                                                                                           |
|----------------------------------|--------------------------------------------------------------------------------------------------------|
| **Doctor**                       | Fast, correct access to their patients' clinical data and imaging; reliable clinical-entry recording.  |
| **Patient**                      | View own data; clear, controllable consent; notification and confirmation of appointments.             |
| **Administrative personnel**     | Schedule appointments and see limited non-clinical data only.                                          |
| **System administrator**         | Manage accounts, groups, and per-group module enablement; account lifecycle control.                   |
| **Software Developer**           | Unambiguous architecture, item decomposition, and interface definitions to implement against.          |
| **QA Engineer**                  | Testable acceptance criteria, traceability, clear module boundaries for unit/integration/system tests. |
| **Regulatory / MDR-FDA Auditor** | Documented, traceable, version-controlled design and risk records; cybersecurity case file.            |
| **Data Protection Officer**      | GDPR principles: lawful consent, minimization, erasure, audit.                                         |
