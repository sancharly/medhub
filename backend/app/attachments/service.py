"""AttachmentService — store and fetch file attachments (TASK-045/046)."""

from __future__ import annotations

import hashlib
import uuid

from app.api.errors import NotFoundError, ValidationProblem
from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.authz.service import AuthorizationService, Resource
from app.core.config import get_settings
from app.db.models.attachment import Attachment
from app.db.models.audit import AuditOutcome
from app.db.repositories.attachment_repo import AttachmentRepository
from app.db.repositories.clinical_repo import ClinicalRepository


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
        data: bytes,
    ) -> Attachment:
        """Upload an attachment for a clinical entry."""
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

        # Size validation
        settings = get_settings()
        max_bytes = getattr(settings, "attachment_max_bytes", 104857600)
        if len(data) > max_bytes:
            raise ValidationProblem(
                f"Attachment size {len(data)} exceeds maximum {max_bytes} bytes."
            )

        # DICOM validation
        is_dicom = content_type == "application/dicom" or filename.lower().endswith(".dcm")
        dicom_meta: dict[str, object] | None = None
        if is_dicom:
            from app.attachments.dicom_validation import validate_dicom  # noqa: PLC0415

            dicom_meta = validate_dicom(data)

        # Compute storage key and checksum
        storage_key = f"attachments/{entry.patient_id}/{uuid.uuid4()}/{filename}"
        checksum = hashlib.sha256(data).hexdigest()

        # Upload to object storage
        self._storage.put_object(storage_key, data, content_type)  # type: ignore[attr-defined]

        # Persist record
        attachment = Attachment(
            clinical_entry_id=entry_id,
            patient_id=entry.patient_id,
            filename=filename,
            content_type=content_type,
            size=len(data),
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

    def open(self, actor: object, attachment_id: uuid.UUID) -> tuple[bytes, str, str]:
        """Fetch attachment bytes. Returns (bytes, content_type, filename)."""
        from app.db.models.account import Account  # noqa: PLC0415

        actor_acct: Account = actor  # type: ignore[assignment]

        attachment = self._attachment_repo.get(attachment_id)
        if attachment is None:
            raise NotFoundError(f"Attachment {attachment_id} not found.")

        self._authz_svc.authorize(
            actor_acct,
            "clinical:read",
            Resource(
                resource_type="attachment",
                owner_id=None,
                patient_id=attachment.patient_id,
            ),
        )

        data = self._storage.get_object(attachment.storage_key)  # type: ignore[attr-defined]
        if data is None:
            raise NotFoundError("Attachment file not found in storage.")

        self._audit_svc.record(
            actor=actor_acct.id,
            action=AuditAction.ATTACHMENT_ACCESS,
            target_type="attachment",
            target_id=str(attachment.id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )
        return data, attachment.content_type, attachment.filename

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
