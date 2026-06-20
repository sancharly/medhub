# ADR-0001: Modular monolith with a runtime plugin/module mechanism

## Status

Accepted

## Context

MedHub must become "the central hub for all clinical activities regardless of specialty", extensible through plugins enabled per user-group by a system administrator (UN-009, UN-010, SR-015, SR-016). At the same time it is a regulated medical device (NFR-005 MDR/FDA, NFR-006 IEC 62304) handling special-category PHI (NFR-004 GDPR, NFR-007 cybersecurity), built by a small prototype-stage team.

The central architectural tension is: **how do we get extensibility without paying the operational, security-surface and traceability cost of a distributed system?**

Forces:

- Extensibility is a first-class product requirement, not speculative (SR-016).
- A medical device benefits from a small, coherent, auditable surface: one access-control choke point, one audit log, one transactional boundary (SR-005, SR-023).
- The team is small; microservices' operational overhead (service mesh, distributed tracing, eventual consistency, per-service compliance) is not justified at prototype scale.
- Consent and access decisions span entities (appointment confirmation grants clinical-data access, SR-035/SR-036) and must be transactionally consistent and immediately effective (SR-008 "revocation takes effect immediately"). Distributed eventual consistency would directly threaten a safety/privacy requirement.

## Decision

Adopt a **modular monolith**: a single deployable backend application internally decomposed into well-bounded modules (software items), plus a **runtime plugin/module mechanism** that lets feature modules (e.g., the DICOM viewer) be added without modifying existing modules.

- One backend process, one primary database, one transactional boundary, one centralized authorization service, one audit log.
- Internal module boundaries are enforced by package structure and an explicit module contract (see ADR-0005), not by network boundaries.
- "Plugin" means an in-process, registered module — not a separately deployed service.

## Consequences

### Positive

- Single authorization choke point (SR-005) and single append-only audit log (SR-023) — strong, coherent compliance story for MDR/FDA/IEC 62304.
- Strong consistency for consent/access transitions (SR-008, SR-036) without distributed-transaction machinery.
- Low operational complexity: one container set, one CI/CD pipeline, one security-review scope (SR-031).
- Extensibility requirement (SR-016) is still met via the module mechanism.

### Negative

- Cannot scale individual modules independently; the whole app scales together (acceptable at prototype scale; revisit if a module like DICOM processing becomes a hotspot).
- A poorly written module shares the process and can affect stability — mitigated by the module contract and access boundary (ADR-0005, SR-016 AC-3).
- Single deployment unit means any module change redeploys the whole backend.

### Neutral

- Module boundaries must be actively maintained in code review to avoid eroding into a "big ball of mud".

## Alternatives Considered

**Microservices (one service per module/domain).** Rejected for the MVP: it multiplies the regulated and security-reviewed surface (each service needs its own auth, audit, TLS, threat model), introduces eventual consistency that conflicts with immediate-revocation requirements (SR-008), and imposes operational overhead unjustified for a small team. Reconsider only if independent scaling or independent regulatory certification of a module becomes a real need.

**Plain monolith (no module mechanism).** Rejected: it fails SR-016, the explicit extensibility requirement, and would force core code changes for every new module.

**Serverless / event-driven.** Rejected: variable-load and async-decoupling drivers are weak here; cold starts harm the DICOM-open latency budget (SR-026 AC-3); event-driven eventual consistency conflicts with immediate consent enforcement.

## References

- Requirements: UN-009, UN-010, SR-005, SR-008, SR-015, SR-016, SR-023, SR-035, SR-036; NFR-004/005/006/007/008
- architecture-designer skill: `assets/architecture-patterns.md`
