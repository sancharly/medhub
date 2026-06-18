# ADR-0007: FHIR-aligned internal data model (FHIR R4), no full FHIR server in MVP

## Status

Accepted

## Context

NFR-002 / SR-021 require that core domain entities (patient, practitioner/doctor, appointment, clinical entry/observation) be **modeled in alignment with their corresponding FHIR resources**, with a documented field mapping, so that future FHIR-based export/import can be added **without redesigning the model**. The requirement is about *data governance and future interoperability*, not about exposing a FHIR API today. SR-026 still demands fast routine operations; a full FHIR server would add weight without a current interoperability requirement.

## Decision

Adopt **FHIR R4** as the **alignment reference** for the internal data model, but do **not** run a full FHIR server or expose a FHIR REST API in the MVP.

- Internal relational tables (ADR-0004) are designed so each core entity maps field-by-field to a FHIR R4 resource: account/person → **Patient** / **Practitioner**, appointment → **Appointment**, clinical entry → **Composition**/**DocumentReference** with **Observation**/**DiagnosticReport** as appropriate, attachments → **DocumentReference.content/Attachment**, consent → **Consent**.
- The mapping is captured in a dedicated **FHIR mapping document** (`docs/specifications/fhir-mapping.md`) and reviewed during design verification (SR-021 AC-2/AC-3).
- The `fhir.resources` Python library provides typed FHIR R4 models used at the (future) export/import boundary; for the MVP it is used to validate the mapping and to shape DTOs, keeping the door open.
- FHIR-specific or rarely-queried fields are stored in JSONB extension columns (ADR-0004) to avoid wide, churny schemas while preserving the mapping.

## Consequences

### Positive

- Satisfies SR-021/NFR-002 (alignment + documented mapping + reviewability) without the cost and latency of a full FHIR server (helps SR-026).
- Future FHIR export/import becomes an additive adapter over an already-aligned model — no redesign (NFR-002 AC-3).
- The internal API can stay ergonomic for the SPA (camelCase DTOs) while remaining FHIR-traceable.

### Negative

- We carry a mapping document that must be kept in sync with schema changes (a design-verification checklist item).
- Not immediately interoperable with external FHIR systems (acceptable — no current requirement; only "future interoperability").

### Neutral

- Terminology bindings (LOINC/SNOMED) are referenced in the mapping but not enforced at MVP; flagged as a post-MVP item.

## Alternatives Considered

**Full FHIR server (e.g., HAPI FHIR, or a FHIR-native datastore).** Rejected for the MVP: heavyweight, adds operational/regulatory surface, and overshoots a requirement that asks only for *alignment and future readiness*. Would also pull the stack toward Java (HAPI), conflicting with ADR-0002.

**Ignore FHIR, model ad-hoc, "map later".** Rejected: directly violates NFR-002/SR-021 and risks a costly future redesign — the exact interoperability risk the requirement calls out.

## References

- Requirements: NFR-002, SR-021; supports UN-008, SR-010, SR-012, SR-013
- Related: ADR-0004; deliverable `docs/specifications/fhir-mapping.md`
