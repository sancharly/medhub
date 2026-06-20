"""FastAPI dependency for AuditService."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.session import get_db


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    return AuditService(AuditRepository(db))
