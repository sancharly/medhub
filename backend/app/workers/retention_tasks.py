"""5-year permanent erasure retention sweep (TASK-036).

Celery Beat task runs daily (configurable via RETENTION_SWEEP_CRON).
Permanently deletes AnonymizedDataset rows where retention_deadline <= now.
Processes in bounded batches; isolates per-dataset failures.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from celery import shared_task
from sqlalchemy import select

logger = logging.getLogger(__name__)

_BATCH_SIZE = 100


@shared_task(  # type: ignore[untyped-decorator]
    name="workers.erase_expired_anonymized_datasets",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def erase_expired_anonymized_datasets(self: object) -> dict[str, int]:
    """Permanently delete expired anonymized datasets.

    Audits ANONYMIZED_DATASET_ERASED per dataset (id + ts; no identifying data).
    Isolates per-dataset failures.
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

    db = next(get_db())
    try:
        # Select expired datasets in bounded batches
        stmt = (
            select(AnonymizedDataset)
            .where(AnonymizedDataset.retention_deadline <= now)
            .limit(_BATCH_SIZE)
        )
        datasets = list(db.execute(stmt).scalars().all())
        audit_svc = AuditService(AuditRepository(db))

        for dataset in datasets:
            dataset_id = str(dataset.id)
            try:
                db.delete(dataset)
                db.flush()
                audit_svc.record(
                    actor=None,
                    action=AuditAction.ANONYMIZED_DATASET_ERASED,
                    target_type="anonymized_dataset",
                    target_id=dataset_id,
                    outcome=AuditOutcome.SUCCESS,
                    ip=None,
                )
                erased += 1
                logger.info(
                    "Anonymized dataset permanently erased",
                    extra={"dataset_id": dataset_id, "ts": now.isoformat()},
                )
            except Exception as exc:
                # Isolate per-dataset failures
                failed += 1
                logger.error(
                    "Failed to erase dataset %s: %s",
                    dataset_id,
                    exc,
                    exc_info=True,
                )
                db.rollback()
                # Re-open fresh transaction for remaining datasets
                db = next(get_db())
                audit_svc = AuditService(AuditRepository(db))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    logger.info("Retention sweep complete", extra={"erased": erased, "failed": failed})
    return {"erased": erased, "failed": failed}
