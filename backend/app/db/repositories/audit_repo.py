"""AuditLog repository — append-only (SR-023). No get/list/update/delete."""

from sqlalchemy.orm import Session

from app.db.models.audit import AuditLog


class AuditRepository:
    """Append-only repository for audit logs.

    Intentionally does NOT inherit from Repository — enforces that only
    add() is available. No read, update, or delete paths (SR-023).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, log: AuditLog) -> AuditLog:
        self._session.add(log)
        self._session.flush()
        return log
