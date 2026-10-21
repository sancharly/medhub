---
id: RISK-003
type: risk
title: DICOM image rendered incorrectly or the wrong study displayed
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
hazard: An imaging study displayed with wrong pixel data, wrong window/level, wrong orientation or laterality, or belonging to another study.
cause: A defect in DICOM parsing, frame selection, transfer-syntax handling or viewport state (or a browser-specific rendering quirk) → the viewer shows an image that does not faithfully represent the acquired data → the clinician interprets it as the patient's image.
harm: Missed or wrong diagnosis leading to wrong or delayed treatment.
severity_initial: 4
probability_initial: 3
severity_residual: 4
probability_residual: 2
acceptability: alarp
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 204452f46017b329884c594ca234277039ce35fcc7bead4b5abe244d9c7dd156
approval_note: self-approved
links:
  - target: SOUP-015
    relation: relates_to
tags:
  - hazard:misinterpretation
  - class:B
---

# RISK-003 — DICOM image rendered incorrectly or the wrong study displayed

## Hazard

An imaging study displayed with wrong pixel data, wrong window/level, wrong orientation or laterality, or belonging to another study.

## Sequence of events

A defect in DICOM parsing, frame selection, transfer-syntax handling or viewport state (or a browser-specific rendering quirk) → the viewer shows an image that does not faithfully represent the acquired data → the clinician interprets it as the patient's image.

## Hazardous situation

A clinician interprets an image that is not, or does not faithfully represent, the patient's study.

## Harm

Missed or wrong diagnosis leading to wrong or delayed treatment.

## Software items involved

SI-MOD-DICOM-BE (pydicom parsing, frame endpoint), SI-MOD-DICOM-FE (viewport, controls), SOUP: pydicom 3.0.2 and the browser rendering stack.

## Initial risk

Severity 4 — Serious (misinterpretation of imaging) — × probability 3 (Occasional) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Render only from the authoritative DICOM object served by the backend, no client-side re-encoding | Design | SR-017 | none yet |
| Explicit, tested viewer controls for window/level, zoom, pan and series navigation | Design | SR-018 | none yet |
| Verification against reference images per supported browser each release | Protective | SR-019, TASK-111 | TS-012 |
| Metadata (patient, study, series) displayed alongside the image so a mismatch is visible | Information for safety | SR-017 | none yet |
| Size and decompression limits on the frame endpoint so a malformed object fails loudly | Protective | SR-031, TASK-135 | TS-008, TS-011 |

## Residual risk

Severity 4 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **alarp**, derived from `risk_matrix`. **The DICOM viewer is not implemented yet** (SR-017/SR-018 belong to the unfinished frontend module phase), so this risk is currently theoretical but its controls are unverified. It must be re-scored, and its verification completed, before any release that ships the viewer.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

Severity is fixed by the clinical use of imaging. Probability is reduced to Remote by rendering only the authoritative object, showing patient/study identity next to the image, and verifying against reference images per browser; MedHub is a viewer for consultation, not a diagnostic workstation, so the clinician confirms findings on the acquiring system when it matters. Further reduction would require diagnostic-grade display certification, out of the intended use. **The viewer is not implemented yet**: this justification must be re-assessed, with the controls verified, before the release that ships it.

## Risks introduced by controls

Strict validation may refuse to display an unusual but valid study, delaying interpretation — RISK-007.
