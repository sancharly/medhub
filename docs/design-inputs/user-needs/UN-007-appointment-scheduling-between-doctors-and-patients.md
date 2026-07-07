---
id: "UN-007"
type: user-need
title: "Appointment scheduling between doctors and patients"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links: []
tags: []
---

## Summary

Doctors, patients, and administrative personnel need to schedule appointments between a doctor and a patient so that consultations are organized at agreed times.

## Description

Coordinating care requires arranging visits. The platform must let appointments be created that link a specific doctor and a specific patient at a specific date and time. The relevant parties need to see the appointments that concern them so they can prepare and attend. This is the operational backbone that connects patients to clinical encounters in the hub.

## Acceptance Criteria

1. An appointment can be created associating one doctor and one patient at a specified date and time.
2. The doctor and patient involved in an appointment can view that appointment.
3. Administrative personnel can create and view appointments on behalf of doctors and patients.

## Risk Analysis

### Rationale

Derived from the MedHub goal "Administrative personal permissions" (scheduling appointments between doctors and patients) and the overall hub purpose of centralizing medical activities.

### Potential Risks

- Operational risk: scheduling errors (wrong participant, wrong time) cause missed or double-booked encounters.
- Privacy risk: appointment lists could reveal care relationships to unauthorized users if not properly scoped.

### Control Measures

- Appointment creation, participant association, and visibility scoping are specified in software requirements traced to this need.
- Visibility is constrained by the role-based access-control mechanism (UN-003).
