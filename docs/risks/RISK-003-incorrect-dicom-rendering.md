---
id: RISK-003
type: risk
title: DICOM image rendered incorrectly or the wrong study displayed
status: in_review
version: "1.4"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-14"
hazard: An imaging study displayed with wrong pixel data, wrong window/level, wrong orientation or laterality, or belonging to another study.
cause: A defect in DICOM parsing, frame selection, transfer-syntax handling or viewport state (or a browser-specific rendering quirk) → the viewer shows an image that does not faithfully represent the acquired data → the clinician interprets it as the patient's image.
harm: Missed or wrong diagnosis leading to wrong or delayed treatment.
severity_initial: 4
probability_initial: 3
severity_residual: 4
probability_residual: 2
acceptability: alarp
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
| Stored-size and declared-decoded-size bounds checked before any pixel data is decoded (150 MiB stored, 1 GiB decoded, CR-006 D-2); a decode that fails part-way returns an RFC 7807 error and no image, so a malformed or truncated object fails loudly and is never shown partly (CR-006, PRB-006). Corrected in 1.2: the 1.1 row named SR-031, TASK-135, TS-008 and TS-011, but no bound was implemented | Protective | SR-017 AC 6; TASK-218 | TS-019 TC-019.1 to TC-019.4 (`backend/modules/dicom_viewer/tests/test_size_bounds.py`; decode stubbed, PRB-048): over-bound stored size and declared decoded size are refused before the read or decode, a truncated pixel stream gives an error and no image, an object exactly at both bounds is not refused. A real render of a 150 MiB reference study is not yet shown |

## Residual risk

Severity 4 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **alarp**, derived from `risk_matrix`. **The DICOM viewer is not implemented yet** (SR-017/SR-018 belong to the unfinished frontend module phase), so this risk is currently theoretical but its controls are unverified. It must be re-scored, and its verification completed, before any release that ships the viewer.

**Change analysis (CR-006, Risk stage, 2026-11-13).** CR-006 realises the size and decode
control (PRB-006, SR-017 AC 6): today `dicom.py` decodes the whole object with no bound, and a
truncated pixel stream is not refused explicitly. The bound adds one cause of its own: a legitimate
study above 150 MiB is refused, which delays interpretation (RISK-007) but never shows a wrong
image. **Expected residual: 4 × 2 → alarp, unchanged**: the viewer is still not deployed
(PRB-048) and the reference-image controls are unverified. Re-scored from the evidence at the
CR-006 verification checkpoint.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

Severity is fixed by the clinical use of imaging. Probability is reduced to Remote by rendering only the authoritative object, showing patient/study identity next to the image, and verifying against reference images per browser; MedHub is a viewer for consultation, not a diagnostic workstation, so the clinician confirms findings on the acquiring system when it matters. Further reduction would require diagnostic-grade display certification, out of the intended use. **The viewer is not implemented yet**: this justification must be re-assessed, with the controls verified, before the release that ships it.

## Risks introduced by controls

Strict validation may refuse to display an unusual but valid study, delaying interpretation — RISK-007.

CR-006 (2026-11-13): the stored and decoded bounds refuse a study above 150 MiB stored or 1 GiB
decoded with an error naming the limit (RISK-007); the design record puts a typical study at 50 to
150 MB, so the bound is above it.

## Version history

- 1.1 (2026-10-21) — Approved (self-approved).
- 1.2 (2026-11-13) — CR-006 Risk stage, §7.4 change analysis (Software Architect role). The size and decompression row is corrected and re-based on SR-017 AC 6 (it named SR-031, TASK-135, TS-008 and TS-011, but no bound existed, PRB-006); planned verification named; expected residual stated; "Risks introduced by controls" extended. Scores unchanged (4 × 2 → alarp). Content change, so the approval record is cleared and the record returns to review.
- 1.3 (2026-11-13) — CR-006 Plan gate (D-22): the size-bounds row names its task, TASK-218. Scores unchanged. Content change, so the approval record is cleared and the record returns to review.
- 1.4 (2026-11-14) — TASK-225 (Document Writer): the Verify column of the size-bounds row names TS-019 TC-019.1 to TC-019.4 (TASK-218) instead of "none yet (planned …)". The tests stub `pixel_array` because NumPy is not installed (PRB-048), so they show the bounds, their order and the error path, not a real render; the 150 MiB reference study is not rendered. Scores unchanged. Content change on an approved record, so the 1.3 approval record is cleared and the record returns to review.
