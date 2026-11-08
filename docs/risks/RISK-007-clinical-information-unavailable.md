---
id: RISK-007
type: risk
title: Clinical information unavailable when needed
status: in_review
version: "1.8"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-07"
hazard: The application, its database, its object storage or its workers unavailable, or attachments unreadable.
cause: Single-host outage, database or object-store failure, exhausted connection pool from a session leak, a missing storage SDK (PRB-002), or an encryption key rotation that makes old rows unreadable → the clinician cannot open the record → they proceed without it or wait.
harm: Delayed care; decisions made without available history. No direct physical harm from the software itself.
severity_initial: 3
probability_initial: 2
severity_residual: 3
probability_residual: 2
acceptability: alarp
links:
  - target: SOUP-020
    relation: relates_to
  - target: SOUP-036
    relation: relates_to
  - target: SOUP-019
    relation: relates_to
  - target: SOUP-014
    relation: relates_to
  - target: SOUP-021
    relation: relates_to
tags:
  - hazard:availability
  - class:B
---

# RISK-007 — Clinical information unavailable when needed

## Hazard

The application, its database, its object storage or its workers unavailable, or attachments unreadable.

## Sequence of events

Single-host outage, database or object-store failure, exhausted connection pool from a session leak, a missing storage SDK (PRB-002), or an encryption key rotation that makes old rows unreadable → the clinician cannot open the record → they proceed without it or wait.

A stored file name that cannot be represented in an HTTP header makes the attachment undownloadable (PRB-063): the download answered 500 for any character outside Latin-1.

Since CR-002 the object store is SeaweedFS ([SOUP-036](../soup/SOUP-036-seaweedfs.md)), replacing
MinIO. Two object-store causes are explicit: an attachment whose stored bytes fail the checksum
check is refused rather than served (SR-013 AC 5), and a lost or changed `AT_REST_ENCRYPTION_KEY`
makes every stored object unreadable, because the store derives its only SSE key from it (SOUP-036
F-4).

## Hazardous situation

A clinician needs clinical information that the system cannot deliver.

## Harm

Delayed care; decisions made without available history. No direct physical harm from the software itself.

## Software items involved

SI-API, SI-PERSIST, SI-ATTACH, SI-WORKER, infrastructure (single-host Compose, ADR-0010).

## Initial risk

Severity 3 — Moderate (care delayed) — × probability 2 (Remote) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Documented backup, monitoring and deployment procedure | Protective | SR-028, TASK-115 | TR-001, TS-013. **Backup part not met:** no backup and restore procedure exists for `postgres_data` or `object_store_data` with its key ([PRB-057](../problem-reports/PRB-057-no-backup-and-restore-procedure.md), major, open, found 2026-10-30 by CR-002 TASK-180) |
| Performance budgets so routine operations stay usable | Design | SR-026 | none yet |
| Worker retries with backoff and no silent enqueue failures | Protective | TASK-141 | none yet |
| Object storage SDK declared as a required runtime dependency and verified in CI | Design | TASK-157 (CR-001, resolves PRB-002) | TS-007 TC-007.5, TS-013 TC-013.8 |
| Key identifier in the ciphertext envelope so rotation cannot orphan rows | Design | SR-022, PRB-004 resolution | TR-001, TS-008 |
| Bucket initialisation ordered after the store is healthy and fail-fast: the backend does not start on a missing or misconfigured bucket (CR-002, PRB-039) | Protective | SR-040 AC 4; TASK-175 (re-run on SeaweedFS by TASK-176) | TS-014 TC-014.4: initialiser starts only after `object-store` is healthy (`docker events` order); an unreachable store gives exit 1 and `backend` stays `Created`; idempotent re-run (TASK-175 and TASK-176 QA reruns) |
| Checksum refusal fails with a clear error, never with partial or wrong content (CR-002) | Protective | SR-013 AC 5; TASK-173 | TS-007 TC-007.6, TC-007.8: 502 `application/problem+json` naming only the attachment id, no object bytes, committed FAILURE audit row; TC-007.7: an unmodified object is served (TASK-173 QA rerun) |
| Field values converted to the identified envelope in one transaction that rolls back if any value does not decrypt; tested against a database populated in the old format; an unknown key id is refused, never decrypted with another key (CR-004, ADR-0018) | Protective | SR-022 AC 6, AC 7; TASK-193, TASK-194 | TS-008 TC-008.9, TC-008.10 (planned) |
| Rotation by a re-encryption command with a `--check` mode, rehearsed on a backup copy before use (CR-004) | Protective | SR-022 AC 8; TASK-195 | TS-008 TC-008.11, rehearsal record (planned) |
| Attachments moved to the separate SSE key by a copy with checksum comparison, source read only, rehearsed on a backup copy (CR-004) | Protective | SR-041 AC 5; TASK-196 | TS-014 TC-014.7, rehearsal record (planned) |
| File names encoded per RFC 6266/5987 with an ASCII fallback; the header is built in one place | Design | SR-013 AC 3; TASK-204 | TS-007 TC-007.9 |
| A file name is refused above 255 UTF-8 bytes at upload, and the `Content-Disposition` value is bounded (about 1 KB) for any stored name, so a long name cannot make the download fail at the proxy (CR-004, PRB-069) | Design | SR-013 AC 1, AC 3; TASK-206 | TS-007 TC-007.11 |
| Dispatch does not wait on a result store (`task_ignore_result`): a Celery `.delay()` with Redis unreachable ends within 5 s instead of about 20 s inside the request's open transaction (CR-004, TASK-206 QA finding 1) | Design | TASK-207 | TS-003 TC-003.7 |
| Retrieval rate limit per originating client address, so one caller cannot block retrieval for all (CR-004, PRB-029) | Design | SR-042 AC 4, AC 5; TASK-186 | TS-016 TC-016.4, TC-016.5 (planned) |

## Residual risk

Severity 3 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **alarp**, derived from `risk_matrix`. Single-host Compose with no high availability is a deliberate MVP decision (arc42 §11, ADR-0010); the residual therefore stays ALARP and needs an explicit human acceptance for each release, with the argument that MedHub is not the only route to the information.

**Change analysis (CR-004, Risk stage, 2026-10-31).** CR-004 both strengthens and threatens
this record. Strengthened: the "key rotation makes old rows unreadable" cause gets its design
control (the row above that names PRB-004 is realised by TASK-193..195), and the shared
rate-limit bucket goes (PRB-029). Threatened, by the change itself: the field migration, the
rotation and the SSE key separation can each make clinical values or attachments unreadable, and
the runtime-role grants can make a statement fail. Each has a fail-safe control above and is an
"ask first" step of CR-004. **Expected residual: 3 × 2 → alarp, unchanged**, set by the
single-host decision (ADR-0010) and PRB-057 as before. Confirmed at verification (TASK-202).

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

Single-host deployment without high availability is a documented MVP decision (ADR-0010, arc42 §11): the product is containerized so HA can be added without redesign. Unavailability delays access but does not corrupt or misattribute information, and the institution's own systems remain available.

**Permanent loss is not covered yet.** A disk loss, a failed upgrade or a lost
`AT_REST_ENCRYPTION_KEY` can lose records and attachments for good, not only delay access, because
no backup and restore procedure exists for `postgres_data`, `object_store_data` and the key
([PRB-057](../problem-reports/PRB-057-no-backup-and-restore-procedure.md), major, open). The
backup part of the first control row is therefore unmet. The `alarp` residual still holds until
then because no release exists and only development data is stored (CR-002 Q-5), so no clinical
record depends on MedHub alone yet. The benefit of shipping the MVP outweighs this residual for the
initial deployment scale only once PRB-057 is resolved or explicitly accepted. **Re-evaluate** when
PRB-057 is resolved or at the first release, whichever comes first; the residual must be
re-accepted at every release.

## Risks introduced by controls

The CR-002 controls of RISK-012 add availability effects to this record, by design:

- The checksum check refuses an attachment whose stored bytes do not match (502). The clinician
  gets a clear error instead of wrong content; the event is audited. Recorded as a control row
  above.
- The credential preflight (TASK-174) and the fail-fast initialiser (TASK-175) stop a deployment
  with a weak key, an unreachable store or a failed bucket set-up. Deployment-time only, with a
  message naming the setting or the step.
- The object store's SSE key is `AT_REST_ENCRYPTION_KEY`; losing or changing it makes the
  attachments unreadable (SOUP-036 F-4). Key handling is RISK-011's; the missing backup and restore
  procedure for the volume and its key is PRB-057.

CR-004 (2026-10-31), availability effects introduced by its controls:

- Start-up refused on a missing, placeholder or invalid secret, on identical field and SSE keys,
  or on an invalid `TRUSTED_PROXIES` entry (deployment time, message names the setting).
- `db-migrate` must complete before the backend and worker start; a failed migration keeps them
  down (fail closed, like the bucket initialiser).
- A table without grants makes the runtime role's statement fail until the next `db-migrate`
  run; `app.db.roles` re-applies grants after every migration (ADR-0017).
- The frontend now listens on 8080; a proxy still pointing at 80 serves nothing. The smoke test
  checks the page through the proxy.

## Version history

- 1.2 (2026-10-21) — Approved (self-approved, 2026-10-21).
- 1.3 (2026-10-22) — CR-001 (TASK-157, PRB-002), change analysis §7.4: the control "Object storage
  dependency declared and verified at startup" is realized as "declared as a required runtime
  dependency and verified in CI" (`boto3` in `[project] dependencies`; the instantiation test
  TS-007 TC-007.5; the production-image import check TS-013 TC-013.8). It is not a check at
  application start. Assessed as equivalent for the cause it targets, a missing SDK, because the
  shipped image is built only from the frozen lock (`uv sync --frozen --no-dev`). Table row updated
  with the implementer and the verification evidence. Scores, `acceptability` and the other
  sections unchanged; residual stays 3 × 2, `alarp`, set by the single-host decision (ADR-0010).
  Approval record cleared; the owner's acceptance is the approval of this version.
- 1.4 (2026-10-30) — CR-002 TASK-181, §7.4 change analysis (CR-002 AC-14), by the Software
  Architect role. Content change, so the approval record is cleared and the record returns to
  review.
  - `cause` and Sequence of events: "MinIO failure" becomes "object-store failure"; the checksum
    refusal and the SSE key loss (SOUP-036 F-4) are named as object-store causes.
  - Link `relates_to` SOUP-022 (obsolete) replaced by SOUP-036 (CR-002 AC-12).
  - Control rows added: bucket initialisation ordered and fail-fast (SR-040 AC 4, TASK-175, TS-014
    TC-014.4) and checksum refusal with a clear error (SR-013 AC 5, TASK-173, TS-007).
  - The backup row records that its backup part is not met (PRB-057).
  - Risks introduced by controls: the CR-002 availability effects listed.
  - Not re-scored: severity 3 × probability 2 → `alarp`, set by the single-host decision
    (ADR-0010). Acceptance is the human's, through approval of this version.
- 1.5 (2026-10-31) — CR-004 Risk stage, §7.4 change analysis (Software Architect role). Control rows added for the CR-004 controls with their planned verification; expected residual stated in "Residual risk"; "Risks introduced by controls" extended. Scores not changed: they are re-scored from the evidence at verification (TASK-202). Content change, so the approval record is cleared and the record returns to review.
- 1.6 (2026-11-06) — CR-004 TASK-204 (PRB-063), §7.4 change analysis: cause "a stored file name that cannot be represented in an HTTP header makes the attachment undownloadable" added to the sequence of events, and one control row (RFC 6266/5987 file names, one header builder; TS-007 TC-007.9). Residual unchanged (3 × 2, `alarp`); this cause was never part of the scored estimate. Content change, so the approval record is cleared and the record returns to review.
- 1.7 (2026-11-07) — TASK-206 (PRB-069): one control row, bounded attachment names and header (TS-007 TC-007.11). Residual unchanged.
- 1.8 (2026-11-07) — TASK-207 (TASK-206 QA finding 1): one control row, dispatch does not wait on a result store (TS-003 TC-003.7). Residual unchanged.
