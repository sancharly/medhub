# TASK-046 — Attachment authorized fetch

- **Phase:** 3 — Domain services
- **Software item / unit:** SI-ATTACH / U-ATT-Fetch
- **Implements:** SR-013 (AC-3 authorized download/open), SR-005 (deny-by-default authorization), SR-022 (in transit / at rest preserved); ADR-0009, ADR-0008
- **Depends on:** TASK-045 (attachment upload), TASK-027 (API deps / authz guard) — must be merged first
- **Branch:** `feature/attachment-fetch`
- **Status:** Not started

## Objective

Stream an attachment's bytes to an authorized user through the backend, enforcing the central authorization check on **every** request. This is the byte source the DICOM module (TASK-073) consumes via `PlatformServices.attachments` — the SPA/module never reads the bucket directly. Traces to SR-013 AC-3, SR-005, SR-022.

## Interfaces to honor

Implements the read half of `AttachmentService` from [12-interfaces.md](../../design/12-interfaces.md) §12.1 **verbatim**:

```python
class AttachmentService:
    def open(self, actor: Account, attachment_id: UUID) -> AttachmentStream: ...   # authorized
    # store(...) is TASK-045
```

`AttachmentStream` carries the byte iterator plus `content_type`, `size`, `filename` for response headers.

- Per §12.3 rule 1, `open` **must** call `AuthorizationService.authorize(actor, "clinical:read", attachment.patient)` before any byte is read — the same consent-union check that gates the parent clinical entry (SR-005, SR-006/SR-007). Deny-by-default; a denied request discloses nothing (SR-005 AC-4).
- Per §12.3 rule 3, only SI-ATTACH talks to object storage. Access is **backend-mediated**: stream the object through the API (ADR-0009 baseline). If a short-lived scoped pre-signed URL is ever used it must be issued only **after** the authorization decision and be short-lived/scoped (ADR-0009 negative note, SR-031 review item) — the MVP default is the authorized stream.

## Implementation detail

- Files to create / modify:
  - `backend/app/attachments/service.py` — add `open`.
  - `backend/app/db/repositories/attachment_repository.py` — `get(attachment_id)`.
  - `backend/app/core/object_storage.py` — add `get_object(key) -> stream` (surgical extension of TASK-013/045 client).
- Endpoint (SI-API): `GET /attachments/{id}` → `StreamingResponse` with the object's `content_type`, `Content-Disposition`, `Content-Length` ([api-design.md](../../specifications/api-design.md)). TLS is terminated at the proxy (SR-022 AC-1) — no plaintext path is served.
- Authorization basis is resolved by `AuthorizationService` from the attachment's `patient_id` (set at upload, TASK-045) — the same union-of-grants logic as clinical reads.
- Audit (SR-023 AC-2 clinical-data access): record `attachment.read` with actor, target patient/attachment, outcome, and authorization basis. Denied attempts are audited too (SR-005, no data).
- Error cases (RFC 7807): unauthorized → `403 /errors/forbidden` (no bytes, no metadata leak); unknown attachment → `404 /errors/not-found`; missing backing object → `404 /errors/not-found`.
- Edge cases: a doctor whose grant was revoked (manual revoke SR-008, or appointment decline SR-036) is denied on the very next fetch because authorization reads live consent (runtime view 6.2/6.6). Range requests (for large DICOM) are out of MVP scope unless TASK-073 requires frame slicing — keep `open` whole-object; frame extraction, if any, is the module's concern via this stream.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/attachments/test_attachment_fetch.py`):
  - authorized user `open` → streams the stored bytes with correct content type/length (SR-013 AC-3).
  - unauthorized user → `403`, no bytes/metadata, denied access audited (SR-005 AC-2/AC-4, SR-023).
  - doctor whose consent was just revoked → next `open` denied (live consent read, SR-008/SR-036).
  - unknown attachment id → `404`.
  - backing object missing → `404`, audited.
  - patient `open` on own attachment → allowed; on another patient's → denied (SR-007).
  - successful and denied fetches audited (SR-023 AC-2).
- Integration (`backend/tests/api/test_attachment_fetch_api.py`): `GET /attachments/{id}` round-trip against MinIO test container through router + authz; revoke-then-fetch returns `problem+json` 403.

## Acceptance criteria

- [ ] An authorized user can download/open an attachment of an entry they may view (SR-013 AC-3).
- [ ] Every fetch passes `AuthorizationService` before bytes are read; deny-by-default (SR-005 AC-1/AC-2).
- [ ] A denied fetch returns 403 and discloses no bytes or metadata (SR-005 AC-4).
- [ ] Access is backend-mediated; the caller never holds bucket credentials (ADR-0009).
- [ ] Revoked consent denies the next fetch (live read, SR-008/SR-036).
- [ ] Successful and denied fetches are audited (SR-023 AC-2).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit + integration tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (fetch endpoint)
- [ ] Audit events emitted for security-relevant actions (SR-023)
- [ ] Traceability matrix row updated (SR-013, SR-005, SR-022 → TASK-046 → tests)
- [ ] Security review completed (authorized byte access / pre-signed URL policy — SR-031.6)
