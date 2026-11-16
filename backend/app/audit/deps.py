"""FastAPI dependency for AuditService."""

from app.audit.service import AuditService
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.session import DbSession


def get_audit_service(db: DbSession) -> AuditService:
    return AuditService(AuditRepository(db))
