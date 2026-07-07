---
id: "UN-008"
type: user-need
title: "Recording clinical entries for a patient"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links: []
tags: []
---

## Summary

A doctor needs to record a clinical entry for a patient, capturing the encounter details and attaching relevant files, so that the patient's clinical record is built up over time.

## Description

After a visit or procedure a doctor must document what happened. A clinical entry captures, at minimum, the date and time, the patient, the authoring doctor, a textual description, and any attached files such as DICOM images, reports, or analysis results. These entries accumulate into the patient's clinical history, which is the core asset of the hub and the basis for continuity of care and information sharing among specialists.

## Acceptance Criteria

1. A doctor can create a clinical entry associated with a specific patient.
2. A clinical entry records at least: date and time, patient, authoring doctor, and a description.
3. A doctor can attach one or more files (for example DICOM images, reports, analysis results) to a clinical entry.
4. Saved clinical entries are retrievable as part of the patient's clinical history by users authorized to view that patient's clinical data.

## Risk Analysis

### Rationale

Derived from the MedHub goal "Clinical entry": doctors can add a clinical entry associated with a patient containing at least date/time, patient, doctor, description, and attached files.

### Potential Risks

- Safety risk: lost, incomplete, or mis-attributed clinical entries can lead to incorrect clinical decisions.
- Data-integrity risk: attaching a file to the wrong patient breaches confidentiality and clinical safety.
- Compliance risk: clinical records must be retained reliably under medical-device and data-protection rules.

### Control Measures

- Clinical-entry fields, file attachment, and patient association are specified in software requirements traced to this need.
- Data integrity and durable storage are reinforced by NFR-002 (FHIR data governance) and NFR-007 (cybersecurity).
- Access to stored entries is gated by the role-based access-control mechanism (UN-004, UN-005).
