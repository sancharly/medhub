# 06 - Runtime View

Critical scenarios that illustrate item interactions, security enforcement, and error/exception behavior. Each links to a PlantUML diagram in `docs/specifications/`.

## 6.1 Login with lockout and session creation (SR-002, SR-029, SR-030)

Diagram: [`../specifications/diagram-seq-login.puml`](../specifications/diagram-seq-login.puml)

- Credentials verified with Argon2id; invalid attempts and non-existent usernames are treated identically (generic error) to prevent enumeration (SR-002.2, SR-029.6).
- 5 consecutive failures lock the account for 30 minutes; lockout is audited (SR-029).
- On success: Redis session created with role-based TTL, 3-session cap enforced, hardened cookie set, success audited (SR-030, SR-023).
- **Error/exception:** locked or invalid → 401 generic; expired absolute lifetime later forces re-auth (SR-030.3).

## 6.2 Doctor views a patient's clinical data (SR-005, SR-006, SR-036)

Diagram: [`../specifications/diagram-seq-doctor-access.puml`](../specifications/diagram-seq-doctor-access.puml)

- Every request resolves the session, then `AuthorizationService` evaluates the **union of active consent grants** for the (doctor, patient) pair (SR-036.3).
- No active grant → deny-by-default 403, access attempt audited, no data disclosed (SR-005.2/4, SR-023.2).
- Active grant (manual or any confirmed appointment) → entries returned, access audited with basis (SR-006.4).

## 6.3 Appointment creation, notification, confirmation → consent; decline scoping (SR-010, SR-035, SR-036)

Diagram: [`../specifications/diagram-seq-appointment-consent.puml`](../specifications/diagram-seq-appointment-consent.puml)

- Creation validates references/datetime, sets PENDING, enqueues dual-channel notification (SR-010, SR-035.1/2/3).
- **Only the patient** can confirm/decline (SR-035.9). Confirm creates an `APPOINTMENT:{id}` consent grant (SR-036.1); the doctor's effective access is the union of all grants.
- Decline deactivates **only** that appointment's grant (Cases A/B/C, SR-036.4): pre-existing manual or other-appointment grants are untouched.
- Every confirm/decline + grant change is audited (SR-035.10, SR-036.6).

## 6.4 Open and view DICOM via the plugin module (SR-015, SR-016, SR-017, SR-018, SR-026)

Diagram: [`../specifications/diagram-seq-dicom-view.puml`](../specifications/diagram-seq-dicom-view.puml)

- The shell shows the viewer nav item only if the module is enabled for one of the user's groups (SR-015.3, SR-016.2); the module loads as a lazy chunk (ADR-0005).
- The byte request passes `ModuleAccessGuard` (enablement) then `AuthorizationService` (consent) (SR-005, SR-015, SR-017.5); the module obtains bytes only through `AttachmentService` (SR-016.3).
- Cornerstone3D applies modality/VOI LUT, orders slices, sets default window/level, renders initial image within 10 s (SR-017.3/4, SR-026.3); user interacts via window/level, zoom, pan, slice nav (SR-018).
- **Error/exception:** not enabled or not authorized → 403, audited; WebGL-incapable browser is out of the supported set (SR-019).

## 6.5 Account creation, activation and lifecycle (SR-032, SR-033, SR-034)

Diagram: [`../specifications/diagram-activity-account-lifecycle.puml`](../specifications/diagram-activity-account-lifecycle.puml)

- Role-constrained creation (admin cannot create sysadmin), unique-email enforcement, INACTIVE state, audited (SR-032).
- Single-use 72 h activation link; user sets policy-compliant password twice; account becomes ACTIVE; audited (SR-033).
- Lifecycle: deactivate (sessions killed ≤30 s, data retained), reactivate, or delete (confirm → anonymize with 5-year retention, email released); all audited (SR-034, SR-024). Deletion detail in 6.7.
- **Error/exception:** expired token → admin resend; password policy/mismatch → rule-specific error (SR-033.3/4).

## 6.6 Patient revokes manual consent (SR-008)

- Patient revokes a `MANUAL` grant via `DELETE /consents/{id}`; the row is deactivated transactionally; subsequent doctor requests are denied **immediately** because authorization reads live consent on each request (SR-008.4). Revoke requires confirmation (SR-027.2) and is audited (SR-008.5).

## 6.7 Account deletion → anonymized retention, and self-service retrieval (SR-024, SR-034, ADR-0013)

Decision: [ADR-0013](adr/0013-account-deletion-anonymized-retention.md). Flow shown in [`../specifications/diagram-activity-account-lifecycle.puml`](../specifications/diagram-activity-account-lifecycle.puml) (delete branch).

- **Delete:** after the SR-034.6 confirmation, `SI-IDENTITY` (`U-ID-Erasure`) severs credentials + PII from the record data and re-keys it into an **anonymized dataset**; the email is released for reuse (SR-034.7). A high-entropy **anonymization code** is generated, sent to the user by email, and **never stored** — only a salted KDF hash is persisted to locate-and-authorize later retrieval (ADR-0011). A 5-year retention deadline is set. The deletion is audited with the anonymized dataset id but never the code (SR-023, SR-024.3).
- **Retrieve (within 5 years):** the (now anonymous) user presents the code; the system derives the same salted hash, matches the anonymized dataset, authorizes retrieval, and audits it. A wrong/lost code cannot retrieve the data — there is no recovery path (by design, ADR-0013).
- **Expiry:** a scheduled `SI-WORKER` job permanently and irreversibly erases any anonymized dataset whose 5-year deadline has passed (SR-024.4).
- **Error/exception:** invalid/expired code → generic denial, audited; expired dataset → not found.
