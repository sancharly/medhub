---
id: "RISK-003"
type: risk
title: "DICOM image rendered incorrectly or the wrong study displayed"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["hazard:misinterpretation", "class:B"]
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

| Severity | Probability (P2) | Risk level (per ADD-003) |
|---|---|---|
| 4 — Serious (misinterpretation of imaging) | 3 — Occasional | 12 — ALARP (12) |

P1 (probability of the software fault itself) is taken as 1 per ADD-003: the fault is assumed to occur.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Render only from the authoritative DICOM object served by the backend, no client-side re-encoding | Design | SR-017 | TS (Release stage) |
| Explicit, tested viewer controls for window/level, zoom, pan and series navigation | Design | SR-018 | TS (Release stage) |
| Verification against reference images per supported browser each release | Protective | SR-019, TASK-111 | TP/TR (Release stage) |
| Metadata (patient, study, series) displayed alongside the image so a mismatch is visible | Information for safety | SR-017 | TS (Release stage) |
| Size and decompression limits on the frame endpoint so a malformed object fails loudly | Protective | SR-031, TASK-135 | TS (Review stage) |

## Residual risk

| Severity | Probability (P2) | Risk level | Acceptable? | Decided by / date |
|---|---|---|---|---|
| 4 — Serious (misinterpretation of imaging) | 2 — Remote | 8 — ALARP (8) | **pending human decision** | — |

**The DICOM viewer is not implemented yet** (SR-017/SR-018 belong to the unfinished frontend module phase), so this risk is currently theoretical but its controls are unverified. It must be re-scored, and its verification completed, before any release that ships the viewer.

## Risks introduced by controls

Strict validation may refuse to display an unusual but valid study, delaying interpretation — RISK-007.
