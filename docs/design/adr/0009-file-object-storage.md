# ADR-0009: S3-compatible object storage (MinIO) with server-side encryption

## Status

Accepted

## Context

Clinical entries carry attachments — DICOM images, reports, analysis results — that can be large and numerous (SR-013, UN-008). These must be stored securely, **encrypted at rest** (SR-013 AC-4, SR-022 AC-2), bound to their entry/patient, and retrievable only through the authorization mechanism (SR-005). Storing large binaries in PostgreSQL (ADR-0004) would bloat the DB, hurt backup/restore and harm performance (SR-026). DICOM viewing streams these objects to the browser (ADR-0008).

## Decision

Store attachment binaries in **S3-compatible object storage**, using **MinIO** for self-hosted/MVP deployments (and any AWS-S3-compatible service in cloud deployments). PostgreSQL holds only `Attachment` metadata (`id`, `clinical_entry_id`, `patient_id`, `filename`, `content_type`, `size`, `storage_key`, `checksum`, `created_at`).

- **Server-side encryption at rest** is enabled on the bucket (SSE; AES-256), satisfying SR-022 AC-2/SR-013 AC-4.
- All access is **mediated by the backend `AttachmentService`**: the SPA/module never holds direct bucket credentials. The backend authorizes each request via `AuthorizationService` (SR-005), then streams the object or issues a short-lived, scoped pre-signed URL. This keeps the SR-005 choke point and SR-023 audit intact (SR-016 AC-3).
- Uploads are validated (content type/size) and the object is bound transactionally to its `Attachment` row and thereby its patient (SR-013 AC-2).

## Consequences

### Positive

- Keeps PostgreSQL lean → better performance and backups (SR-026), while large DICOM/report files live where object storage excels.
- Bucket-level SSE provides encryption at rest with simple key management (SR-022 AC-3) without per-row crypto complexity.
- Backend-mediated access preserves authorization and audit for every file fetch (SR-005, SR-023), and supplies the authorized byte stream the DICOM viewer needs (ADR-0008).
- S3 compatibility avoids cloud lock-in: MinIO locally, managed S3 in production, same code.

### Negative

- A second storage system to operate, secure, and back up (mitigated: MinIO ships as one container in the Compose stack, ADR-0010).
- Pre-signed URLs, if used, must be short-lived and scoped to avoid leaking access beyond an authorization decision (a security-review checklist item, SR-031).
- Cross-store consistency (DB row vs. object) must be handled (write object then commit metadata; orphan-cleanup job).

### Neutral

- Retention/erasure (SR-024, SR-034) operates on both the metadata row and the object; the erasure capability must delete/anonymize both.

## Alternatives Considered

**Binaries in PostgreSQL (BYTEA / large objects).** Rejected: DB bloat, slow backups, memory pressure streaming large DICOM, worse performance (SR-026).

**Local filesystem on the app server.** Rejected: doesn't scale across replicas, weaker encryption/lifecycle tooling, complicates containerized/portable deployment (ADR-0010).

**Cloud-only (hard dependency on AWS S3).** Rejected as the baseline: forces a cloud vendor for an MVP that should also run self-hosted in a hospital; S3-compatible MinIO gives portability while remaining S3-API-compatible for later cloud moves.

## References

- Requirements: UN-008, SR-005, SR-013, SR-022, SR-023, SR-024, SR-026, SR-034; NFR-004, NFR-007
- Related: ADR-0004, ADR-0008, ADR-0010, ADR-0011
