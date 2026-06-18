# FHIR R4 Mapping Specification

Implements **SR-021** / **NFR-002**: core domain entities are modeled in alignment with FHIR R4 resources, with a documented field mapping so future FHIR export/import can be added without redesigning the model (ADR-0007). This document is a design-verification artifact and must be reviewed against the FHIR R4 resource definitions and kept in sync with schema/migration changes.

FHIR version: **R4 (4.0.1)**. Library: `fhir.resources` (Python). The MVP does **not** expose a FHIR API; this mapping governs the internal model and the future export/import adapter boundary.

## Entity → FHIR resource overview

| MedHub entity | FHIR R4 resource | Notes |
|---------------|------------------|-------|
| `Account` (user_type=PATIENT) | `Patient` | Demographics + identifier |
| `Account` (user_type=DOCTOR) | `Practitioner` | Practitioner identity |
| `Account` (ADMIN / SYSADMIN) | `Practitioner` + `PractitionerRole` (administrative) | Non-clinical roles; minimal demographics |
| `Appointment` | `Appointment` | participants = doctor + patient |
| `ClinicalEntry` | `Composition` (+ `DocumentReference`) | encounter note; observations/reports referenced |
| `Attachment` | `DocumentReference.content[].attachment` / `Binary` | binary in object store (ADR-0009) |
| `ConsentGrant` | `Consent` | patient-granted access to a practitioner |

## Field mappings

### Account → Patient / Practitioner

| MedHub field | FHIR path | Notes |
|--------------|-----------|-------|
| `id` | `Patient.identifier` / `Practitioner.identifier` | system-assigned business identifier |
| `email` | `...telecom[system=email].value` | unique username (SR-003) |
| `first_name` | `...name[0].given[0]` | |
| `surname` | `...name[0].family` | |
| `date_of_birth` | `Patient.birthDate` / `Practitioner.birthDate` | admin-visible field (SR-009) |
| `user_type` | resource type + `PractitionerRole.code` | drives RBAC (SR-004) |
| `status` | `Patient.active` / `Practitioner.active` | ACTIVE→true; others→false |

### Appointment → Appointment

| MedHub field | FHIR path | Notes |
|--------------|-----------|-------|
| `id` | `Appointment.identifier` | |
| `scheduled_at` | `Appointment.start` | (`end` derivable) |
| `state` | `Appointment.status` | PENDING→`pending`, CONFIRMED→`booked`, DECLINED→`cancelled` (SR-035) |
| `doctor_id` | `Appointment.participant[actor=Practitioner]` | |
| `patient_id` | `Appointment.participant[actor=Patient]` | |
| confirmation | `participant[actor=Patient].status` | accepted/declined/needs-action |

### ClinicalEntry → Composition / DocumentReference

| MedHub field | FHIR path | Notes |
|--------------|-----------|-------|
| `id` | `Composition.identifier` | |
| `patient_id` | `Composition.subject (Patient)` | |
| `author_doctor_id` | `Composition.author (Practitioner)` | set from session, not client (SR-012.3) |
| `occurred_at` | `Composition.date` | |
| `description` | `Composition.section[].text` | |
| attachments | `Composition.section[].entry -> DocumentReference` | see Attachment |

### Attachment → DocumentReference / Binary

| MedHub field | FHIR path | Notes |
|--------------|-----------|-------|
| `filename` | `DocumentReference.content.attachment.title` | |
| `content_type` | `...attachment.contentType` | `application/dicom` for DICOM |
| `size` | `...attachment.size` | |
| `checksum` | `...attachment.hash` | integrity |
| `storage_key` | `...attachment.url` (internal ref) | resolves to object store (ADR-0009) |

### ConsentGrant → Consent

| MedHub field | FHIR path | Notes |
|--------------|-----------|-------|
| `patient_id` | `Consent.patient` | data subject |
| `doctor_id` | `Consent.provision.actor.reference (Practitioner)` | grantee |
| `source` | `Consent.provision.purpose` / extension | MANUAL vs APPOINTMENT:{id} (SR-036) |
| `active` | `Consent.status` | active→`active`, revoked→`inactive` |
| `created_at` / `revoked_at` | `Consent.dateTime` / provision period | audit-aligned (SR-008) |

## Deferred / post-MVP

- Terminology bindings (LOINC, SNOMED CT, ICD) referenced but not enforced at MVP.
- Granular `Observation` / `DiagnosticReport` decomposition of clinical entries (MVP keeps `Composition` + attachments).
- A FHIR REST API (`/fhir`) and bulk export — additive over this aligned model.

## Verification

- Reviewer confirms each MedHub field has a FHIR path or a documented rationale for omission (SR-021.2).
- Review is recorded in the design-verification record (SR-021.3).
