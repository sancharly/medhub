# 11 - Risks and Technical Debt

## Architectural risks & mitigations

| Risk                                               | Impact                                                  | Mitigation                                                                                                        |
|----------------------------------------------------|---------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Centralized AuthZ is high blast-radius**         | A bug in `SI-AUTHZ` could leak PHI or wrongly deny care | Most rigorous unit/integration tests incl. negative cases; deny-by-default; security review (SR-005, SR-031.6)    |
| **In-process modules share the runtime**           | A faulty module could destabilize the host              | Modules are trusted/reviewed code at MVP; access only via `PlatformServices`; no untrusted hot-loading (ADR-0005) |
| **DICOM rendering correctness is safety-critical** | Misrender → clinical misinterpretation                  | Use vetted Cornerstone3D; verify against reference images in system test (SR-017, NFR-005)                        |
| **Consent per-source union complexity**            | Mis-scoped decline could strip legitimate access        | Model grants by source; transactional union query; explicit tests for SR-036 Cases A/B/C                          |
| **Single-host Compose = no HA**                    | Outage blocks clinical workflows (UN-001)               | Acceptable at MVP; containerized so HA is additive; backups + monitoring documented (ADR-0010)                    |
| **Cross-store consistency (DB ↔ object store)**    | Orphaned/dangling attachments                           | Write object then commit metadata; orphan-cleanup job (ADR-0009)                                                  |
| **Safari WebGL/Cornerstone quirks**                | Viewer defects on one browser (SR-019)                  | Cross-browser test pass each release; documented support matrix                                                   |
| **Async email delivery failures**                  | Missed activation/appointment notice                    | Retries in Celery; admin resend (SR-033.7); dual-channel in-app + email (SR-035.3)                                |

## Known technical debt / deferred items (deliberate MVP scope)

| Item                                                         | Why deferred                                              | Future path                                                                           |
|--------------------------------------------------------------|-----------------------------------------------------------|---------------------------------------------------------------------------------------|
| Full FHIR REST server & external interoperability            | No current interop requirement; only "future readiness"   | Additive adapter over aligned model (ADR-0007, fhir-mapping.md)                       |
| PACS / DICOMweb (WADO-RS/QIDO-RS)                            | Authorized attachment endpoint suffices for MVP           | Cornerstone3D already speaks DICOMweb (ADR-0008)                                      |
| Multi-tenancy & HA orchestration (Kubernetes)                | Single-tenant simpler & safer for PHI at MVP              | Containerized → incremental migration (ADR-0010)                                      |
| External IdP/IAM (Keycloak/Auth0)                            | Precise SR behaviors simple to implement/audit in-process | Optional later (ADR-0011, ADR-0012)                                                   |
| Untrusted / hot-loaded plugins                               | Severe security risk, not required                        | Sandbox/iframe/microservice isolation if ever needed (ADR-0005)                       |
| Terminology bindings (LOINC/SNOMED)                          | Not required for MVP model                                | Bind in FHIR mapping post-MVP                                                         |
| Formal IEC 62366 usability engineering & penetration testing | Beyond MVP; basic usability controls applied              | Expand per NFR-009 note                                                               |
| Notification delivery/read tracking                          | Best-effort send confirmed for MVP (no proof of delivery) | Add via `Notification` `status`/hook extension point, no caller rework (section 8.12) |
