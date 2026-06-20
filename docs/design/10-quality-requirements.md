# 10 - Quality Requirements

## Quality scenarios (testable)

| Quality attribute                | Scenario                                                                      | Target / acceptance                                              | Source                 |
|----------------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------|------------------------|
| **Security — access control**    | A doctor requests a patient's clinical data with no active consent grant      | Denied (403), no data disclosed, attempt audited                 | SR-005, SR-006, SR-023 |
| **Security — consent immediacy** | Patient revokes a grant, doctor immediately re-requests                       | Subsequent request denied immediately                            | SR-008.4               |
| **Security — consent scoping**   | Doctor has manual grant + appointment grant; patient declines the appointment | Doctor retains manual access (Case B)                            | SR-036.4               |
| **Security — credentials**       | Set 11-char or single-class password                                          | Rejected with rule-specific error                                | SR-025                 |
| **Security — lockout**           | 5 consecutive failed logins                                                   | Account locked 30 min; generic error; audited                    | SR-029                 |
| **Security — session**           | 15 min doctor inactivity                                                      | Session expires; 2-min warning shown beforehand                  | SR-030                 |
| **Security — deactivation**      | Sysadmin deactivates an active user                                           | Active sessions invalidated within 30 s                          | SR-034.2               |
| **Security — transport/at rest** | Inspect traffic and storage                                                   | All traffic TLS; attachments encrypted at rest                   | SR-001, SR-022         |
| **Safety — DICOM correctness**   | Open a known CT/MRI study                                                     | Correct scaling, default window/level, slice order vs. reference | SR-017                 |
| **Safety — attribution**         | Doctor creates clinical entry                                                 | Author = authenticated user, not client-supplied                 | SR-012.3               |
| **Compliance — traceability**    | Audit the design                                                              | Every SR traced UN/NFR→SR→architecture item→test                 | SR-028, NFR-006        |
| **Extensibility**                | Add a new module                                                              | New package + registry entry, no edits to existing modules       | SR-016.1               |
| **Reach — cross-browser**        | Run core workflows on Safari/Firefox/Chrome/Edge                              | No functional errors, layout intact                              | SR-019                 |
| **Reach — responsive**           | Core workflows on phone/tablet/desktop                                        | Operable, no horizontal scroll of primary content                | SR-020                 |
| **Usability**                    | Each user type does its core task                                             | Completable with on-screen guidance only                         | SR-027.4               |
| **Performance — routine**        | List appointments / clinical entries                                          | < 3 s under normal load                                          | SR-026.1               |
| **Performance — DICOM**          | Open a typical study                                                          | Initial rendered image < 10 s                                    | SR-026.3               |

## "Normal load" — MVP working assumption (pending stakeholder confirmation)

SR-026 defines its budgets "under normal load" but gives no figures. To make the performance scenarios above objective and testable, the following concrete values are adopted as a **labeled assumption for a single-tenant medical-center prototype**. They are engineering assumptions, **not confirmed requirements**, and are pending stakeholder confirmation; the performance tests verify against these numbers until they are revised.

| Parameter                    | Assumed MVP value                                                                    | Notes                                                                      |
|------------------------------|--------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| Concurrent active users      | **50** (peak ~100)                                                                   | One medical center; doctors + admin + patients active together             |
| Sustained API request rate   | **~10 req/s** (peak ~25 req/s)                                                       | Routine interactive traffic, excludes bulk uploads                         |
| Typical DICOM study          | **CT/MRI ~150–300 slices**, ~512×512, **~50–150 MB**; X-ray a single ~10–30 MB image | "Initial rendered image < 10 s" (SR-026.3) is first-slice, not full-volume |
| Clinical entries per patient | up to **~500** historical entries                                                    | Bounds list/pagination performance (SR-026.1)                              |
| Routine-op response target   | **< 3 s** at the above concurrency (SR-026.1/2)                                      | Page nav, listings, save clinical entry                                    |
| Single deployment host       | commodity VM, **e.g. 4 vCPU / 8–16 GB RAM**                                          | Matches single-host Docker Compose MVP (ADR-0010)                          |

These are the figures performance/system tests (SR-026.4) target until a stakeholder provides authoritative numbers; revising them does not change the architecture, only the test thresholds.

## Quality goal priority (from section 01)

1. Security & Privacy → 2. Safety/Correctness → 3. Compliance/Traceability → 4. Extensibility → 5. Usability/Reach.

Where goals conflict, the higher-priority goal wins. Example: a stricter session timeout (security) is mandated even though it slightly burdens usability — mitigated by the required 2-minute warning (SR-030.4).
