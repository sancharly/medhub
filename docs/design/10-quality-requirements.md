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
| **Security — session cap**       | Ten logins for one account start at the same moment                           | At most 3 live sessions remain; a login that cannot be applied answers 503 and stores no session | SR-030 AC 7            |
| **Security — decision point**    | A role comparison that decides access is added outside `backend/app/authz/`   | A static test fails; every decision, allowed or denied, leaves an audit row with the source address | SR-005, SR-023 AC 6, AC 7 |
| **Security — audit integrity**   | The runtime role runs `UPDATE`, `DELETE` or `TRUNCATE` on `audit_log`; a secret is passed as a target id | Permission error (SQLSTATE 42501); `AuditFieldError` before any row is written | SR-023 AC 8, AC 9      |
| **Security — client address**    | A request from an untrusted peer carries a forged `X-Forwarded-For`           | The peer address is used; the retrieval limit counts 5 attempts per address per 3600 s | SR-042                 |
| **Security — secrets**           | Start the stack with an unset, empty or placeholder secret, or equal field and SSE keys | Compose or the service stops, naming the setting, never the value | SR-041                 |
| **Security — key rotation**      | Rotate the field key with the application running, interrupt the command, run it again | Every value stays readable throughout; the second run converts the rest; a retired key cannot be removed while a value needs it | SR-022 AC 6 to AC 8    |
| **Security — logs**              | Use an activation link, force a 500 and an upstream error, then search all service logs | No activation token, session or CSRF token, password, retrieval code or `.env` secret appears (residual: section 11) | SR-043                 |
| **Security — route guard**       | A user opens a route outside their role                                       | Not mounted; redirected to `/profile`; the server still refuses the data | SR-005, SR-009         |
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
| **Performance — concurrency**    | 20 authenticated clients issue mixed reads and writes at once against one API worker | No 5xx and no worker kill; the 3 s budgets hold; a slow database or object-store call does not delay unrelated requests (baseline `8028685`: 210 transport errors and 10 worker kills; after TASK-136: 0 and 0) | SR-026 AC 5 (D-3), TS-018 |
| **Performance — data-access cost** | List a user's groups for 1, 10 and 100 memberships; look up by appointment time, consent appointment, patient, clinical entry or doctor | Constant number of queries; the query plan uses the index (migrations 0011, 0012) | SR-026 AC 6, TS-018 TC-018.7, TC-018.8 |
| **Performance — initial payload** | `npm run build` on the production configuration                              | Initial JavaScript at most 165 kB gzip (160.1 kB after TASK-145; 172.55 kB before); each lazy route group is its own chunk; the build fails otherwise | SR-026 AC 7, TS-018 TC-018.10 |
| **Resilience — bounded attachment IO** | Upload a file over 150 MiB; download an object changed between the two reads; open a DICOM study over 150 MiB stored or 1 GiB decoded | Upload refused after at most the limit plus one chunk; download refused as 502 before any byte, or aborted; DICOM refused before decoding, no partial image | SR-013 AC 5, AC 6; SR-017 AC 6 |
| **Resilience — acknowledged writes** | A commit fails after the handler returned                                    | The client receives a 5xx, not the success status; an immediate read after a 2xx finds the write | SR-012 AC 5, SR-023 AC 10 |
| **Security — session deadline**  | The client idle timer runs while the server session is slid or not             | The client deadline is never later than the server's; `GET /me/modules` polling does not extend the session; at the client timeout the server session is ended | SR-030 AC 1, AC 2, AC 8 |

## Load figures that bind the tests (CR-006)

SR-026 AC 5 fixes the concurrency test at **20 authenticated clients on one API worker** (CR-006 D-3), with 20 threads and 40 connections deployed (section 7). The figures below remain the planning assumption for the other budgets; the 50 concurrent users of that table are not the SR-026 AC 5 test, which is the stricter, measurable one. Attachment bounds: **150 MiB** per attachment (`attachment_max_bytes`, D-2) and, for the DICOM viewer, **150 MiB stored and 1 GiB decoded** (`dicom_max_stored_bytes`, `dicom_max_decoded_bytes`). SR-026 AC 8 (inactivity tracking re-armed at most once per second) describes activity tracking that the client no longer has; whether the criterion is moot is an open decision of CR-006 (P-20).

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
