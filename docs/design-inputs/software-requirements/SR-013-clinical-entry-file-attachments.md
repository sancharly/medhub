---
id: SR-013
type: software-requirement
title: Clinical entry file attachments
status: approved
version: "1.5"
author: Carlos Santiago Liceras
created: "2026-07-07"
updated: "2026-11-13"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-13"
approved_digest: 7223b3a4dc52389c515297ac2134d65a80670d139c1186f39a1ed878c2c60385
approval_note: self-approved
links:
  - target: RISK-002
    relation: mitigates
  - target: RISK-003
    relation: mitigates
  - target: RISK-012
    relation: mitigates
  - target: RISK-007
    relation: mitigates
  - target: UN-008
    relation: derives_from
tags:
  - control:design
---

## Summary

The system shall allow a doctor to attach one or more files (e.g., DICOM images, reports, analysis results) to a clinical entry and authorized users to retrieve them.

## Description

This requirement implements file attachment for clinical entries. When creating or editing a clinical entry, a doctor can attach one or more files. Attachments are stored securely, associated with the entry and thereby the patient, and are retrievable by users authorized to view that patient's clinical data. The system accepts DICOM image files among other formats.

## Acceptance Criteria

1. A doctor can attach one or more files to a clinical entry, including DICOM image files.
2. Each attachment is associated with its clinical entry and the entry's patient.
3. An authorized user can download or open an attachment of an entry they are permitted to view.
4. Attachments are stored encrypted at rest and access is subject to the authorization mechanism.
5. On every download or open of an attachment, including a DICOM study, the system computes the SHA-256 of the content retrieved from the object store and compares it with the checksum stored when the attachment was uploaded. On a mismatch the content is not served, the client receives an error response that does not disclose the content, and an audit event with outcome FAILURE is recorded naming the attachment and the actor (SR-023). A matching checksum changes nothing for the user.
6. Uploading and downloading an attachment do not hold the whole object in the memory of the API process: content is handled in bounded chunks. An upload larger than the maximum attachment size is refused with an RFC 7807 error without reading more than that size plus one chunk. The checksum rule of AC 5 continues to hold for every download.

## Origin Requirement

Derived from: User Need UN-008 "Recording clinical entries for a patient".

## Risk Analysis

### Rationale

Imaging and report files are essential clinical content; reliable, secure attachment and retrieval are required for care and for the DICOM viewer to operate on real data.

### Potential Risks

- Data-integrity risk: an attachment linked to the wrong patient breaches safety and confidentiality.
- Security risk: unprotected file storage exposes health data.
- Integrity risk: an object substituted or planted in the object store by an actor who bypasses the application (RISK-012) is shown to a clinician as the original attachment or DICOM study (harms of RISK-002 and RISK-003).
- Availability risk: the checksum check rejects an attachment whose stored object was altered; the clinician sees an error instead of the study (RISK-007), which is the intended failure mode.

### Control Measures

- Bind attachments to their entry/patient; encrypt at rest (SR-022); gate retrieval via SR-005.
- DICOM rendering provided by SR-017/SR-018.
- Verify the stored SHA-256 checksum on every download and fail loudly on a mismatch (AC 5; risk control of RISK-012, CR-002). A negative test with a substituted object verifies it.

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-002 (risk register bootstrap, TASK-147). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.2 (2026-10-21) — Tagged `control:design` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.3 (2026-10-30) — Content change, so the approval is cleared and the record returns to review (CR-002). Added AC 5 (checksum verified on download) and `mitigates` links to RISK-003 and RISK-012. Reason: the SHA-256 checksum computed at upload (`backend/app/attachments/service.py:79`) is never checked on read, so a substituted object is served as the original (PRB-043, RISK-012).
- 1.4 (2026-11-13) — Content change, so the approval is cleared and the record returns to review (CR-006, GitHub sancharly/medhub#28). Added AC 6 (bounded memory on upload and download; the size limit enforced while the body is read). Reason: the size limit was checked after the whole body was read into memory, and concurrent large transfers exhaust the API process (PRB-008; RISK-007).
- 1.5 (2026-11-13) — Traceability change at the CR-006 Risk gate R-3: added the `mitigates` link to RISK-007. Returned to review for the human's re-approval; AC text unchanged.
