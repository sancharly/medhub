---
id: RISK-003
type: risk
title: DICOM image rendered incorrectly or the wrong study displayed
status: in_review
version: "1.6"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-25"
hazard: An imaging study displayed with wrong pixel data, wrong window/level, wrong orientation or laterality, or belonging to another study.
cause: A defect in DICOM parsing, frame selection, transfer-syntax handling or viewport state (or a browser-specific rendering quirk), an object in a transfer syntax the backend cannot decode faithfully being decoded anyway, or decoded pixel data served under a media type that presents it as a DICOM object → the viewer shows an image that does not faithfully represent the acquired data → the clinician interprets it as the patient's image.
harm: Missed or wrong diagnosis leading to wrong or delayed treatment.
severity_initial: 4
probability_initial: 3
severity_residual: 4
probability_residual: 2
acceptability: alarp
links:
  - target: SOUP-015
    relation: relates_to
  - target: SOUP-037
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

Two transfer-syntax causes are explicit since CR-008 (2026-11-25), when the backend frame path becomes
reachable and decodes for real for the first time (PRB-048, PRB-046):

- An object whose transfer syntax the module cannot decode faithfully — a compressed syntax with no
  decoder installed, a lossy syntax, an unknown UID, or no declared syntax that pydicom would guess — is
  decoded anyway, or partly, and the result is returned as frame N.
- The decoded samples of a frame (raw array bytes with no header) are labelled `application/dicom`, as
  the endpoint did before CR-008, so a consumer could read them as a DICOM object and misinterpret them.

## Hazardous situation

A clinician interprets an image that is not, or does not faithfully represent, the patient's study.

## Harm

Missed or wrong diagnosis leading to wrong or delayed treatment.

## Software items involved

SI-MOD-DICOM-BE (pydicom parsing, frame endpoint; ADD-015), SI-MOD-DICOM-FE (viewport, controls; ADD-022), SOUP: pydicom 3.0.2 (SOUP-015), NumPy 2.5.5 (SOUP-037, decoded frame arrays, from CR-008) and the browser rendering stack.

## Initial risk

Severity 4 — Serious (misinterpretation of imaging) — × probability 3 (Occasional) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Render only from the authoritative DICOM object served by the backend, no client-side re-encoding | Design | SR-017 | none yet: not verifiable on 2026-11-15, the DICOM module is not installed in the started stack (`dicom_viewer` absent, no `medhub.modules` entry point; PRB-048) and NumPy is missing (PRB-046), so no real render can be made; the viewer phase is unfinished. CR-008 makes the backend half verifiable: the whole-object path returns the stored object byte-for-byte (SR-017 AC 8; TASK-235, TS-019 TC-019.10, planned); the browser half stays with the viewer phase (#29) |
| Explicit, tested viewer controls for window/level, zoom, pan and series navigation | Design | SR-018 | none yet: the viewer controls are not implemented (SR-018 belongs to the unfinished viewer phase) |
| Verification against reference images per supported browser each release | Protective | SR-019, TASK-111 | TS-012 |
| Metadata (patient, study, series) displayed alongside the image so a mismatch is visible | Information for safety | SR-017 | none yet: not verifiable on 2026-11-15, the DICOM module is not installed in the started stack (`dicom_viewer` absent, no `medhub.modules` entry point; PRB-048) and NumPy is missing (PRB-046), so no real render can be made; the viewer phase is unfinished |
| Stored-size and declared-decoded-size bounds checked before any pixel data is decoded (150 MiB stored, 1 GiB decoded, CR-006 D-2); a decode that fails part-way returns an RFC 7807 error and no image, so a malformed or truncated object fails loudly and is never shown partly (CR-006, PRB-006). Corrected in 1.2: the 1.1 row named SR-031, TASK-135, TS-008 and TS-011, but no bound was implemented | Protective | SR-017 AC 6; TASK-218 | TS-019 TC-019.1 to TC-019.4 (`backend/modules/dicom_viewer/tests/test_size_bounds.py`; decode stubbed, PRB-048): over-bound stored size and declared decoded size are refused before the read or decode, a truncated pixel stream gives an error and no image, an object exactly at both bounds is not refused. A real render of a 150 MiB reference study is not yet shown |
| Transfer-syntax allow-list checked before any decode: `?frame=N` is served only for Implicit VR Little Endian, Explicit VR Little Endian, Deflated Explicit VR Little Endian, Explicit VR Big Endian and RLE Lossless (all lossless, decoded by pydicom and NumPy without a plugin, CR-008 D-3 (a)); any other UID, or none, is refused from the file meta information alone with an RFC 7807 400, rule `dicom_transfer_syntax_unsupported`, naming the UID, no pixel bytes, `pixel_array` never called; order stored size, then transfer syntax, then declared decoded size, then decode (CR-008, PRB-046) | Design | SR-017 AC 10, AC 6; TASK-234 | TS-019 TC-019.6 (JPEG Baseline, JPEG 2000, unknown and missing UID refused; negative control: allow-list removed and the tests fail) and TC-019.8 (check order) — planned, TASK-234 |
| Frame response correctly labelled and exact: a decoded frame is `application/octet-stream` with a documented layout (C order, native byte order, dtype from BitsAllocated and PixelRepresentation, ADD-015), never `application/dicom`; its bytes equal the known sample values of frame N for single- and multi-frame objects in every supported syntax (CR-008 D-4) | Design | SR-017 AC 9; TASK-235 | TS-019 TC-019.9 (real decodes on generated fixtures, compared with the known values) and TC-019.11 (frame out of range) — planned, TASK-235; system level TC-019.5 backend frame part, TASK-239 |
| No user-interface control presents a download as opening the viewer: the "Open in viewer" link is removed, Download stays, until the viewer phase (#29) adds an entry point that obtains the study only through the module endpoint (CR-008 D-5) | Information for safety | SR-017 AC 11; TASK-237 | TS-019 TC-019.12 (`AttachmentItem` tests) — planned, TASK-237 |
| The operator documentation names the transfer syntaxes the frame path decodes and states that others are refused there but still downloadable whole (CR-008 P-2) | Information for safety | SR-017 AC 10; TASK-238 | Review of `infra/DEPLOY.md` (TASK-238 QA); information for safety, no automated test |

## Residual risk

Severity 4 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **alarp**, derived from `risk_matrix`. **The DICOM viewer is not implemented yet** (SR-017/SR-018 belong to the unfinished frontend module phase), so this risk is currently theoretical but its controls are unverified. It must be re-scored, and its verification completed, before any release that ships the viewer.

**Change analysis (CR-006, Risk stage, 2026-11-13).** CR-006 realises the size and decode
control (PRB-006, SR-017 AC 6): today `dicom.py` decodes the whole object with no bound, and a
truncated pixel stream is not refused explicitly. The bound adds one cause of its own: a legitimate
study above 150 MiB is refused, which delays interpretation (RISK-007) but never shows a wrong
image. **Expected residual: 4 × 2 → alarp, unchanged**: the viewer is still not deployed
(PRB-048) and the reference-image controls are unverified. Re-scored from the evidence at the
CR-006 verification checkpoint (TASK-226, 2026-11-15): TS-019 TC-019.1 to TC-019.4 passed on the branch head (the DICOM module suite, 31 passed) and the started stack confirmed that the module is not installed and NumPy is absent, so the reference-image controls are still unverified and the viewer is still not deployed; **4 × 2 → alarp, unchanged**.

**Change analysis (CR-008, Risk stage, 2026-11-25; §7.4).** CR-008 installs the DICOM module in every
environment (PRB-048) and makes its frame path decode for real with NumPy (PRB-046). It adds no hazard
and does not change the class (B): it adds two causes to the existing hazard, an unsupported or
mis-identified transfer syntax decoded anyway and a decoded frame mislabelled as a DICOM object, and
gives each a design control (the allow-list refusal before decoding, SR-017 AC 10; the
`application/octet-stream` label and exact-value tests, AC 9). The D-3 (a) list is lossless only, so a
supported frame equals the acquired samples, and every syntax that needs a decoder plugin is refused, so
no decoder plugin — and none of its defects — is SOUP (SOUP-015, SOUP-037: no relevant anomaly on
2026-11-25). The PRB-006 bounds are kept and get one real decode at a small size (TASK-235). The control
"render only from the authoritative object" becomes verifiable on the backend side (whole-object path,
AC 8). The frontend viewer is still not built (#29), and the reference-image and metadata controls are
still unverified, so the residual is not lowered. **Expected residual: 4 × 2 → alarp, unchanged**
(`risk_matrix` row 4, column 2). Initial risk unchanged (4 × 3 → alarp): the new causes sit inside the
existing transfer-syntax cause. Accepted by the human on 2026-11-25 with its ALARP argument (CR-008 D-B;
recorded, the MedTrace approval of this record confirms it). Re-scored from the evidence at the CR-008 verification task (TASK-239).

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

Severity is fixed by the clinical use of imaging. Probability is reduced to Remote by rendering only the authoritative object, showing patient/study identity next to the image, and verifying against reference images per browser; MedHub is a viewer for consultation, not a diagnostic workstation, so the clinician confirms findings on the acquiring system when it matters. Further reduction would require diagnostic-grade display certification, out of the intended use. **The viewer is not implemented yet**: this justification must be re-assessed, with the controls verified, before the release that ships it.

## Risks introduced by controls

Strict validation may refuse to display an unusual but valid study, delaying interpretation — RISK-007.

CR-006 (2026-11-13): the stored and decoded bounds refuse a study above 150 MiB stored or 1 GiB
decoded with an error naming the limit (RISK-007); the design record puts a typical study at 50 to
150 MB, so the bound is above it.

CR-008 (2026-11-25): the allow-list refuses `?frame=N` for every compressed syntax other than RLE
Lossless (JPEG family, JPEG-LS, JPEG 2000, HTJ2K, video) and for an object with no declared syntax. A
clinician cannot get a server-decoded frame of such a study; the whole object stays available
(AC 8) and the planned viewer decodes it in the browser (ADR-0008). This delays nothing today: no
frontend consumer of the frame path exists (CR-008 A-5). Removing the "Open in viewer" link (AC 11)
leaves Download as the only route to a study until the viewer phase; the link never rendered before
(PRB-048), so no user loses a function.

## Version history

- 1.1 (2026-10-21) — Approved (self-approved).
- 1.2 (2026-11-13) — CR-006 Risk stage, §7.4 change analysis (Software Architect role). The size and decompression row is corrected and re-based on SR-017 AC 6 (it named SR-031, TASK-135, TS-008 and TS-011, but no bound existed, PRB-006); planned verification named; expected residual stated; "Risks introduced by controls" extended. Scores unchanged (4 × 2 → alarp). Content change, so the approval record is cleared and the record returns to review.
- 1.3 (2026-11-13) — CR-006 Plan gate (D-22): the size-bounds row names its task, TASK-218. Scores unchanged. Content change, so the approval record is cleared and the record returns to review.
- 1.4 (2026-11-14) — TASK-225 (Document Writer): the Verify column of the size-bounds row names TS-019 TC-019.1 to TC-019.4 (TASK-218) instead of "none yet (planned …)". The tests stub `pixel_array` because NumPy is not installed (PRB-048), so they show the bounds, their order and the error path, not a real render; the 150 MiB reference study is not rendered. Scores unchanged. Content change on an approved record, so the 1.3 approval record is cleared and the record returns to review.
- 1.5 (2026-11-15) — TASK-226 (CR-006 verification): the three "none yet" rows say why no evidence exists (viewer not installed, PRB-048; NumPy missing, PRB-046; controls unimplemented); the TS-019 run dated; re-scored, 4 × 2 → alarp, unchanged. Content change, so the record stays `in_review` for the owner's acceptance.
- 1.6 (2026-11-25) — CR-008 Risk stage, §7.4 change analysis (Software Architect role). `cause` and Sequence of events: the unsupported or mis-identified transfer syntax decoded anyway, and the mislabelled frame. Four control rows added (allow-list before decode, SR-017 AC 10, TASK-234; exact and correctly labelled frame, AC 9, TASK-235; no false viewer control, AC 11, TASK-237; supported syntaxes in DEPLOY.md, TASK-238), each with planned verification; the authoritative-object row notes the backend half (AC 8, TASK-235). Link `relates_to` SOUP-037 (NumPy). Expected residual stated; "Risks introduced by controls" extended. Scores unchanged (4 × 3 → 4 × 2, alarp). Content change, so the approval record is cleared and the record returns to review.
