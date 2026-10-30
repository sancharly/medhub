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

    def add_independent(self, log: AuditLog) -> AuditLog:
        """Persist ``log`` on its own short-lived session, committed at once (ADR-0016).

        The row is not part of the request transaction, so it survives the request ending
        in an error. A failure to write raises.
        """
        with Session(bind=self._session.get_bind()) as own:
            own.add(log)
            own.commit()
        return log
