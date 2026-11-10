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
| **Object store component has a high advisory rate and rolling releases** | A vulnerable or unpatched store exposes PHI objects (RISK-012) | SeaweedFS pinned by digest; no console; unused listeners off; isolated internal network; credential preflight; default encryption verified in CI; stored checksum verified on download; advisories read monthly and fixes adopted by a reviewed digest change (ADR-0015, PLAN-002, SOUP-036) |
| **Async email delivery failures**                  | Missed activation/appointment notice                    | Retries in Celery; admin resend (SR-033.7); dual-channel in-app + email (SR-035.3); the API binds the configured Celery app (PRB-071); enqueue fails within about a second when Redis is unreachable |
| **Field key lost or exposed**                      | A lost key makes `clinical_entry.description` unrecoverable; an exposed key weakens it | Key identifier in every value and a rehearsed rotation (ADR-0018, RISK-011); no backup of the key or the data exists yet, so a lost key is final (PRB-057) |
| **A wrong `TRUSTED_PROXIES` fails silently**       | Every audit address and rate-limit key becomes the proxy's | Fixed subnet and proxy address in Compose, a test that the three values agree, a started-stack check (ADR-0019, TS-016) |
| **Runtime role grants lag a new table**            | A statement fails with a permission error until the next `db-migrate` | `db-migrate` grants every table on each run; the stack does not start without it (ADR-0017, RISK-007) |

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

## Open problem reports and residuals that bound the design

Open at the time of CR-004 (the records are authoritative; this table says what each one limits):

| Record | Limit on the design | Note |
|--------|--------------------|------|
| [PRB-013](../problem-reports/PRB-013-silent-enqueue-failure.md) (major) | A failed enqueue is logged at two call sites (WARNING with ids) but no task is retried or recorded as lost | Stays open (CR-004 D-18) |
| [PRB-057](../problem-reports/PRB-057-no-backup-and-restore-procedure.md) (major) | No backup and restore procedure for `postgres_data` or `object_store_data`. It still bounds key loss: a lost `AT_REST_ENCRYPTION_KEY`, retired key or `OBJECT_STORE_SSE_KEY` cannot be recovered, and the damaged-row procedure in `infra/DEPLOY.md` depends on a backup the operator makes alone | The statement that backups are documented (ADR-0010) was untrue; see its note |
| [PRB-060](../problem-reports/PRB-060-allowed-authz-audit-row-rolled-back-when-request-fails.md) (minor) | An allowed authorization decision leaves no audit row when the request then fails | Human accepted for now; fix together with PRB-058 |
| [PRB-058](../problem-reports/PRB-058-independent-audit-write-lost-on-pool-exhaustion.md) (minor) | An independent audit write can be lost when the connection pool is exhausted | |
| [PRB-072](../problem-reports/PRB-072-concurrent-writes-collapse-the-api.md) (major) | About twenty parallel writes on a healthy stack answer 502 and kill the worker; the root cause is not established. Bounds the "normal load" assumption of section 10 | Outside CR-004 (D-18); related to PRB-009 |
| [PRB-073](../problem-reports/PRB-073-attachment-name-with-dot-segments-answers-500.md) (minor) | An attachment name with dot segments answers 500; containment relies on the object store's refusal because the display name and the storage key are one value | Outside CR-004 |
| [PRB-074](../problem-reports/PRB-074-credentials-and-email-in-celery-task-arguments.md) (major) | Activation tokens, retrieval codes and an erased user's e-mail address sit in Redis as plaintext task arguments | Outside CR-004; no requirement covers credentials at rest in the broker |
| [PRB-075](../problem-reports/PRB-075-backend-fails-to-start-when-an-enabled-module-disappears.md) (major) | The backend does not start when a module with group enablement rows is uninstalled or its manifest is rejected (registry delete hits a foreign key) | See the residual on module discovery below |

Residuals for the release's residual-anomaly evaluation (human decisions; the requirement text is not edited):

- **SR-043 AC 4 (CR-004 D-19):** a hand-crafted `Referer` that carries a token, or a token in the query string of another path, sent to a non-activation location during an upstream failure or a 413, is written to the proxy error log. No MedHub URL or browser flow produces it.
- **Reverse proxy master as UID 0:** the official nginx image used as the internet-facing proxy is not built by MedHub and runs its master process as root (PRB-007; human to accept at release).
- **Unused settings in two services:** `celery-beat` receives object-store and field-key settings it does not use, and `db-migrate` receives object-store settings it does not use (it does use the field keyring: migration 0010 and `reencrypt --verify-key-ids`), because the start-up rule checks them. Accept or plan narrowing (open decision).
- **Module discovery and registry sync can stop the start (PRB-075):** a rejected manifest only logs a WARNING and the module is skipped, but the registry sync then deletes the row of every module no longer discovered (rejected or uninstalled). The delete fails on a foreign key (`fk_group_module_enablement_module_id`, no `ON DELETE`) whenever any group has an enablement row for the module, enabled or not; the lifespan logs `Module registry sync failed at startup` and re-raises, so the backend does not start. Remedy today: fix the manifest or reinstall the previous module version (`infra/DEPLOY.md`, step 4). Decision needed: how a removed or rejected module is retired, and whether a rejected manifest should log at ERROR naming the entry point.

## Closed technical debt

| Item | Closed by | Note |
|------|-----------|------|
| Object store: MinIO community edition unmaintained, with unfixed advisories, floating tags and a console | CR-002 (ADR-0015, SeaweedFS 4.51 by digest) | The replacement's own debt is the monthly advisory cadence above. Hosts that held attachments in MinIO migrate once (`infra/DEPLOY.md`) |
