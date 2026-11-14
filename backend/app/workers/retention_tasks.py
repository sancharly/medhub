"""5-year permanent erasure retention sweep (TASK-036, TASK-141).

Celery Beat task runs daily (configurable via RETENTION_SWEEP_CRON).
Permanently deletes AnonymizedDataset rows where retention_deadline <= now.
Processes in bounded batches. Each dataset gets its own database session and transaction, so a
failure is isolated to its dataset and every session is closed (SR-024 AC 5). A failed dataset
makes the task retry itself, at most ``max_retries`` times; the deadline is re-checked inside the
dataset's own session, so a retry never deletes a dataset that is not expired. The dataset row
is locked (``SELECT ... FOR UPDATE``) with the deadline re-checked in the same statement, so two
overlapping sweeps erase a dataset once and write one audit row (PRB-084).
Logs carry dataset ids and counts only (SR-043).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from celery import shared_task
from sqlalchemy import select

logger = logging.getLogger(__name__)

_BATCH_SIZE = 100
_MAX_RETRIES = 3
_RETRY_BACKOFF = 300  # seconds base; doubled per retry, as the e-mail tasks' exponential backoff


def _locked_due_dataset(dataset_id: Any, now: datetime) -> Any:
    """The dataset row, locked, only if it still exists and its deadline has passed.

    Plain ``FOR UPDATE`` (not ``SKIP LOCKED``): a second sweep waits for the first one's
    transaction and then re-evaluates the row, so a dataset is never skipped.
    """
    from app.db.models.anonymized_dataset import AnonymizedDataset  # noqa: PLC0415

    return (
        select(AnonymizedDataset)
        .where(AnonymizedDataset.id == dataset_id, AnonymizedDataset.retention_deadline <= now)
        .with_for_update()
    )


@shared_task(  # type: ignore[untyped-decorator]
    name="workers.erase_expired_anonymized_datasets",
    bind=True,
    max_retries=_MAX_RETRIES,
    default_retry_delay=_RETRY_BACKOFF,
)
def erase_expired_anonymized_datasets(self: Any) -> dict[str, int]:
    """Permanently delete expired anonymized datasets.

    Audits ANONYMIZED_DATASET_ERASED per dataset (id + ts; no identifying data).
    A dataset that fails is counted and the sweep continues; if any failed, the task retries.
    """
    from app.audit.actions import AuditAction  # noqa: PLC0415
    from app.audit.service import AuditService  # noqa: PLC0415
    from app.db.models.anonymized_dataset import AnonymizedDataset  # noqa: PLC0415
    from app.db.models.audit import AuditOutcome  # noqa: PLC0415
    from app.db.repositories.audit_repo import AuditRepository  # noqa: PLC0415
    from app.db.repositories.session import get_db  # noqa: PLC0415

    now = datetime.now(UTC)
    erased = 0
    failed = 0

    # Session 1: the ids of the expired datasets (a bounded batch), nothing else.
    db = next(get_db())
    try:
        stmt = (
            select(AnonymizedDataset.id)
            .where(AnonymizedDataset.retention_deadline <= now)
            .limit(_BATCH_SIZE)
        )
        dataset_ids = list(db.execute(stmt).scalars().all())
    finally:
        db.close()

    for dataset_id in dataset_ids:
        # One session and transaction per dataset: closed on every path.
        db = next(get_db())
        try:
            # Locked, and re-checked inside this session: erased meanwhile (by an overlapping
            # sweep, which this one waited for), or not expired -> no row, leave it.
            stmt = _locked_due_dataset(dataset_id, datetime.now(UTC))
            dataset = db.execute(stmt).scalar_one_or_none()
            if dataset is None:
                continue
            db.delete(dataset)
            db.flush()
            AuditService(AuditRepository(db)).record(
                actor=None,
                action=AuditAction.ANONYMIZED_DATASET_ERASED,
                target_type="anonymized_dataset",
                target_id=str(dataset_id),
                outcome=AuditOutcome.SUCCESS,
                ip=None,
            )
            db.commit()
            erased += 1
            logger.info(
                "Anonymized dataset permanently erased",
                extra={"dataset_id": str(dataset_id), "ts": now.isoformat()},
            )
        except Exception as exc:
            failed += 1
            db.rollback()
            # Id and exception class only: the exception text is not logged.
            logger.error(
                "Failed to erase anonymized dataset %s (%s)", dataset_id, type(exc).__name__
            )
        finally:
            db.close()

    logger.info("Retention sweep complete", extra={"erased": erased, "failed": failed})

    if failed:
        retries = self.request.retries
        if retries < self.max_retries:
            raise self.retry(countdown=_RETRY_BACKOFF * 2**retries)
        logger.error(
            "Retention sweep gave up after %d retries; datasets not erased: %d",
            self.max_retries,
            failed,
        )
    return {"erased": erased, "failed": failed}
