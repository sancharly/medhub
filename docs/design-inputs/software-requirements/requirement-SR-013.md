# SR-013 Clinical entry file attachments

## Summary

The system shall allow a doctor to attach one or more files (e.g., DICOM images, reports, analysis results) to a clinical entry and authorized users to retrieve them.

## Description

This requirement implements file attachment for clinical entries. When creating or editing a clinical entry, a doctor can attach one or more files. Attachments are stored securely, associated with the entry and thereby the patient, and are retrievable by users authorized to view that patient's clinical data. The system accepts DICOM image files among other formats.

## Acceptance Criteria

1. A doctor can attach one or more files to a clinical entry, including DICOM image files.
2. Each attachment is associated with its clinical entry and the entry's patient.
3. An authorized user can download or open an attachment of an entry they are permitted to view.
4. Attachments are stored encrypted at rest and access is subject to the authorization mechanism.

## Origin Requirement

Derived from: User Need UN-008 "Recording clinical entries for a patient".

## Risk Analysis

### Rationale

Imaging and report files are essential clinical content; reliable, secure attachment and retrieval are required for care and for the DICOM viewer to operate on real data.

### Potential Risks

- Data-integrity risk: an attachment linked to the wrong patient breaches safety and confidentiality.
- Security risk: unprotected file storage exposes health data.

### Control Measures

- Bind attachments to their entry/patient; encrypt at rest (SR-022); gate retrieval via SR-005.
- DICOM rendering provided by SR-017/SR-018.

## Status

Approved

## Version History

Version 1.0 - Initial creation
