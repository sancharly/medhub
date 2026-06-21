from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings


def _parse_cron(cron_expr: str) -> crontab:
    """Parse a 5-field cron string into a celery.schedules.crontab."""
    parts = cron_expr.split()
    if len(parts) != 5:
        raise ValueError(f"Expected 5-field cron expression, got: {cron_expr!r}")
    minute, hour, day_of_month, month_of_year, day_of_week = parts
    return crontab(
        minute=minute,
        hour=hour,
        day_of_month=day_of_month,
        month_of_year=month_of_year,
        day_of_week=day_of_week,
    )


settings = get_settings()

celery_app = Celery(
    "medhub",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Retry defaults
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Beat schedule
    beat_schedule={
        "erase-expired-anonymized-datasets": {
            "task": "workers.erase_expired_anonymized_datasets",
            "schedule": _parse_cron(settings.retention_sweep_cron),
        },
    },
)

# Autodiscover tasks in all worker sub-modules
celery_app.autodiscover_tasks(
    [
        "app.workers.email_tasks",
        "app.workers.session_tasks",
        "app.workers.retention_tasks",
    ]
)
