---
id: "SR-010"
type: software-requirement
title: "Appointment creation"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "UN-007"
    relation: derives_from
tags: []
---

## Summary

The system shall allow an authorized user to create an appointment that associates one doctor and one patient at a specified date and time.

## Description

This requirement implements appointment creation. An appointment record links exactly one doctor and one patient and stores a date and time. Administrative personnel, and the involved doctor and patient (per visibility rules), can create appointments. The system validates that the referenced doctor and patient exist and that the date/time is provided.

## Acceptance Criteria

1. An authorized user can create an appointment specifying a doctor, a patient, and a date/time.
2. The system rejects an appointment that is missing the doctor, the patient, or the date/time.
3. A created appointment is persisted and retrievable.
4. Administrative personnel can create appointments without accessing clinical data.

## Origin Requirement

Derived from: User Need UN-007 "Appointment scheduling between doctors and patients".

## Risk Analysis

### Rationale

Appointment creation is the operational mechanism that connects patients to clinical encounters in the hub.

### Potential Risks

- Operational risk: invalid or incomplete appointments cause scheduling failures.
- Privacy risk: scheduling must not require or expose clinical data.

### Control Measures

- Validate required fields and entity references on creation.
- Restrict administrative-personnel data access via SR-009; visibility governed by SR-011.
