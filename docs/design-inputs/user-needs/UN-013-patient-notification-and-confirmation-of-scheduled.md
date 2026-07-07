---
id: "UN-013"
type: user-need
title: "Patient notification and confirmation of scheduled appointments"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links: []
tags: []
---

## Summary

A patient needs to be notified when an appointment is scheduled for them and must be able to confirm their attendance before the appointment takes place, so that they retain control over which consultations they participate in and which doctors may access their clinical data.

## Description

Appointments in MedHub may be created by administrative personnel or doctors on behalf of the patient. Without an active notification and confirmation step, a patient could be enrolled in an appointment — and implicitly expose their clinical data to a doctor — without their knowledge or explicit consent. Patients must receive a timely notification and be given the opportunity to confirm or decline each appointment. Confirming an appointment constitutes the patient's explicit consent for the associated doctor to access their clinical data for that care relationship.

## Acceptance Criteria

1. A patient receives a notification when a new appointment is created that involves them.
2. A patient can view all pending appointments and confirm or decline each one.
3. Confirming an appointment grants the associated doctor access to the patient's clinical data.
4. An unconfirmed appointment does not grant the doctor access to the patient's clinical data.

## Risk Analysis

### Rationale

GDPR requires that consent to process sensitive health data (clinical records) be freely given, specific, informed, and unambiguous. Automatic data access on appointment creation — without an active patient consent step — is not unambiguous consent. The confirmation workflow establishes a clear consent event that is auditable and traceable to the specific appointment and doctor.

### Potential Risks

- **Compliance:** Granting clinical data access to a doctor without explicit patient action conflicts with GDPR lawful-basis requirements for processing health data.
- **Privacy:** A patient who is unaware that an appointment was created in their name is unaware that a doctor may be accessing their clinical records.
- **Safety:** If a patient cannot decline a wrongly created appointment, a doctor may access clinical data under a mistaken care relationship.

### Control Measures

- Notification and confirmation workflow ensure the patient is informed and takes an explicit action before any clinical data is shared.
- The confirmation event is recorded in the audit log, providing a traceable consent record.
- The revoke mechanism (SR-008) remains available after confirmation, giving the patient the ability to withdraw consent at any time.
