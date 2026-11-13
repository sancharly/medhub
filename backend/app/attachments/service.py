"""AttachmentService — store and fetch file attachments (TASK-045/046)."""

from __future__ import annotations

import hashlib
import hmac
import uuid
from collections.abc import Iterator
from typing import BinaryIO

from app.api.errors import (
    AttachmentIntegrityError,
    NotFoundError,
    ProblemDetail,
    ValidationProblem,
)
from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.authz.service import AuthorizationService, Resource
from app.core.config import get_settings
from app.core.object_storage import ObjectChangedError
from app.db.models.attachment import Attachment
from app.db.models.audit import AuditOutcome
from app.db.repositories.attachment_repo import AttachmentRepository
from app.db.repositories.clinical_repo import ClinicalRepository

MAX_FILENAME_BYTES = 255
_CHUNK_SIZE = 65536  # 64 KiB


class AttachmentService:
    def __init__(
        self,
        attachment_repo: AttachmentRepository,
        clinical_repo: ClinicalRepository,
        audit_svc: AuditService,
        authz_svc: AuthorizationService,
        object_storage: object,
    ) -> None:
        self._attachment_repo = attachment_repo
        self._clinical_repo = clinical_repo
        self._audit_svc = audit_svc
        self._authz_svc = authz_svc
        self._storage = object_storage

    def store(
        self,
        actor: object,
        entry_id: uuid.UUID,
        filename: str,
        content_type: str,
        file: BinaryIO,
    ) -> Attachment:
        """Upload an attachment for a clinical entry, read from ``file`` in bounded chunks."""
        from app.db.models.account import Account  # noqa: PLC0415

        actor_acct: Account = actor  # type: ignore[assignment]

        entry = self._clinical_repo.get(entry_id)
        if entry is None:
            raise NotFoundError(f"Clinical entry {entry_id} not found.")

        self._authz_svc.authorize(
            actor_acct,
            "clinical:write",
            Resource(
                resource_type="attachment",
                owner_id=None,
                patient_id=entry.patient_id,
            ),
        )

        # Size validation and checksum in one bounded pass (SR-013 AC 6): read in chunks, hash
        # incrementally, refuse as soon as the count passes the maximum.
        max_bytes = get_settings().attachment_max_bytes
        digest = hashlib.sha256()
        size = 0
        while chunk := file.read(_CHUNK_SIZE):
            size += len(chunk)
            if size > max_bytes:
                raise ValidationProblem(f"Attachment size exceeds maximum {max_bytes} bytes.")
            digest.update(chunk)
        file.seek(0)
        checksum = digest.hexdigest()

        # File name bound (SR-013 AC 1, PRB-069): refused, never truncated, as the stored name is
        # part of the clinical record (SR-013 AC 2). 255 bytes is NAME_MAX and bounds the header.
        if len(filename.encode("utf-8", "surrogatepass")) > MAX_FILENAME_BYTES:
            raise ValidationProblem(
                "The file name is longer than 255 bytes.",
                errors=[
                    ProblemDetail(
                        field="file",
                        rule="filename_max_bytes",
                        message="The file name is longer than 255 bytes.",
                    )
                ],
            )

        # DICOM validation
        is_dicom = content_type == "application/dicom" or filename.lower().endswith(".dcm")
        dicom_meta: dict[str, object] | None = None
        if is_dicom:
            from app.attachments.dicom_validation import validate_dicom  # noqa: PLC0415

            dicom_meta = validate_dicom(file)

        storage_key = f"attachments/{entry.patient_id}/{uuid.uuid4()}/{filename}"

        # Upload to object storage: one PutObject, the file as body
        self._storage.put_object(storage_key, file, size, content_type)  # type: ignore[attr-defined]

        # Persist record
        attachment = Attachment(
            clinical_entry_id=entry_id,
            patient_id=entry.patient_id,
            filename=filename,
            content_type=content_type,
            size=size,
            storage_key=storage_key,
            checksum=checksum,
            dicom_metadata=dicom_meta,
        )
        try:
            self._attachment_repo.add(attachment)
        except Exception:
            # Roll back object storage upload on DB failure
            try:
                self._storage.delete_object(storage_key)  # type: ignore[attr-defined]
            except Exception:
                pass
            raise

        self._audit_svc.record(
            actor=actor_acct.id,
            action=AuditAction.ATTACHMENT_UPLOAD,
            target_type="attachment",
            target_id=str(attachment.id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )
        return attachment

    def open_stream(
        self, actor: object, attachment_id: uuid.UUID
    ) -> tuple[Iterator[bytes], str, str, int]:
        """Two-pass bounded download: (chunks, content_type, filename, size).

        Pass 1 hashes the object chunk by chunk, keeping nothing, and records its ETag. On a match,
        pass 2 re-reads it with ``If-Match: <ETag>`` and serves the chunks, hashing again; an
        object replaced between the passes (412) or a digest that differs at the end of pass 2 is
        the SR-013 AC 5 failure path. Memory does not grow with the object (SR-013 AC 6,
        ADR-0021, CR-006 D-10).
        """
        from app.db.models.account import Account  # noqa: PLC0415

        actor_acct: Account = actor  # type: ignore[assignment]
        attachment = self._authorized_attachment(actor_acct, attachment_id)

        def _refuse() -> AttachmentIntegrityError:
            self.record_access_failure(actor_acct, attachment.id)
            return AttachmentIntegrityError(
                f"Attachment {attachment_id} failed its integrity check and was not served."
            )

        try:
            chunks, etag = self._storage.get_object_stream(attachment.storage_key)  # type: ignore[attr-defined]
            digest = hashlib.sha256()
            for chunk in chunks:
                digest.update(chunk)
        except Exception:
            self.record_access_failure(actor_acct, attachment.id)
            raise
        if not hmac.compare_digest(digest.hexdigest(), attachment.checksum):
            raise _refuse()

        try:
            chunks, _ = self._storage.get_object_stream(  # type: ignore[attr-defined]
                attachment.storage_key, if_match=etag
            )
        except ObjectChangedError:
            raise _refuse() from None
        except Exception:
            self.record_access_failure(actor_acct, attachment.id)
            raise

        self._audit_svc.record(
            actor=actor_acct.id,
            action=AuditAction.ATTACHMENT_ACCESS,
            target_type="attachment",
            target_id=str(attachment.id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )

        def _verified() -> Iterator[bytes]:
            # The last chunk is held back until the digest of the whole pass has matched, so a
            # tampered pass 2 never completes the declared Content-Length: the client sees a short,
            # aborted transfer, not a complete 200 (SR-013 AC 5, ADR-0021).
            served = hashlib.sha256()
            count = 0
            held: bytes | None = None
            try:
                for chunk in chunks:
                    if not chunk:
                        continue
                    count += len(chunk)
                    if count > attachment.size:
                        # More bytes than were stored: stop before anything further is sent
                        # (the held chunk included), so Content-Length is never satisfied.
                        raise _refuse()
                    served.update(chunk)
                    if held is not None:
                        yield held
                    held = chunk
                if count != attachment.size or not hmac.compare_digest(
                    served.hexdigest(), attachment.checksum
                ):
                    raise _refuse()
                if held is not None:
                    yield held
            finally:
                # Starlette does not close a sync iterator when the client disconnects.
                chunks.close()

        return _verified(), attachment.content_type, attachment.filename, attachment.size

    def _authorized_attachment(self, actor: object, attachment_id: uuid.UUID) -> Attachment:
        attachment = self._attachment_repo.get(attachment_id)
        if attachment is None:
            raise NotFoundError(f"Attachment {attachment_id} not found.")

        self._authz_svc.authorize(
            actor,  # type: ignore[arg-type]
            "clinical:read",
            Resource(
                resource_type="attachment",
                owner_id=None,
                patient_id=attachment.patient_id,
            ),
        )
        return attachment

    def open(
        self, actor: object, attachment_id: uuid.UUID, max_bytes: int | None = None
    ) -> tuple[bytes, str, str]:
        """Fetch attachment bytes. Returns (bytes, content_type, filename).

        With ``max_bytes``, an attachment stored larger than that is refused before any read
        (SR-017 AC 6: the module path holds the object in memory).
        """
        from app.db.models.account import Account  # noqa: PLC0415

        actor_acct: Account = actor  # type: ignore[assignment]
        attachment = self._authorized_attachment(actor_acct, attachment_id)

        if max_bytes is not None and attachment.size > max_bytes:
            raise ValidationProblem(
                f"The attachment is larger than the maximum of {max_bytes} bytes for this use."
            )

        try:
            data = self._storage.get_object(attachment.storage_key)  # type: ignore[attr-defined]
        except Exception:
            self.record_access_failure(actor_acct, attachment.id)
            raise
        if data is None:
            self.record_access_failure(actor_acct, attachment.id)
            raise NotFoundError("Attachment file not found in storage.")

        # SR-013 AC 5: never serve bytes that differ from what was uploaded (RISK-012).
        actual = hashlib.sha256(data).hexdigest()
        if not hmac.compare_digest(actual, attachment.checksum):
            self.record_access_failure(actor_acct, attachment.id)
            raise AttachmentIntegrityError(
                f"Attachment {attachment_id} failed its integrity check and was not served."
            )

        self._audit_svc.record(
            actor=actor_acct.id,
            action=AuditAction.ATTACHMENT_ACCESS,
            target_type="attachment",
            target_id=str(attachment.id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )
        return data, attachment.content_type, attachment.filename

    def record_access_failure(self, actor: object, attachment_id: uuid.UUID) -> None:
        """Record that an authorized download of an existing attachment did not complete.

        SR-023 AC 2 / ADR-0016: a FAILURE row is independent, so it survives the request's
        rollback. ``ip=None`` uses the request's client address (SR-023 AC 6).
        """
        self._audit_svc.record(
            actor=actor.id,  # type: ignore[attr-defined]
            action=AuditAction.ATTACHMENT_ACCESS,
            target_type="attachment",
            target_id=str(attachment_id),
            outcome=AuditOutcome.FAILURE,
            ip=None,
        )

    def list_attachments(self, actor: object, entry_id: uuid.UUID) -> list[Attachment]:
        """List attachments for a clinical entry."""
        from app.db.models.account import Account  # noqa: PLC0415

        actor_acct: Account = actor  # type: ignore[assignment]

        entry = self._clinical_repo.get(entry_id)
        if entry is None:
            raise NotFoundError(f"Clinical entry {entry_id} not found.")

        self._authz_svc.authorize(
            actor_acct,
            "clinical:read",
            Resource(
                resource_type="attachment",
                owner_id=None,
                patient_id=entry.patient_id,
            ),
        )

        self._audit_svc.record(
            actor=actor_acct.id,
            action=AuditAction.ATTACHMENT_ACCESS,
            target_type="attachment",
            target_id=str(entry_id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )
        return self._attachment_repo.list_for_clinical_entry(entry_id)
