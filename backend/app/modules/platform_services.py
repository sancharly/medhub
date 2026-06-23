"""PlatformServices — request-scoped bundle of core services exposed to modules (TASK-071)."""

from __future__ import annotations

from dataclasses import dataclass

from app.attachments.service import AttachmentService
from app.audit.service import AuditService
from app.authz.service import AuthorizationService
from app.clinical.service import ClinicalDataService


@dataclass
class PlatformServices:
    authorization: AuthorizationService
    clinical: ClinicalDataService
    attachments: AttachmentService
    audit: AuditService
