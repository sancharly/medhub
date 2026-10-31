---
id: SR-013
type: software-requirement
title: Clinical entry file attachments
status: approved
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-07-07"
updated: "2026-10-30"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-30"
approved_digest: 5f1662f9657b7a87c708c2834567aa0a3e82cbd1fcf2c220debf3706dba2c360
approval_note: self-approved
links:
  - target: RISK-002
    relation: mitigates
  - target: RISK-003
    relation: mitigates
  - target: RISK-012
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
