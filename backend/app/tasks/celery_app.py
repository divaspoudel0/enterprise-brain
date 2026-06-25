from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "enterprise_brain",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "scan-risks-hourly": {
            "task": "app.tasks.tasks.scheduled_risk_scan",
            "schedule": crontab(minute=0),
        },
        "refresh-forecasts-daily": {
            "task": "app.tasks.tasks.scheduled_forecast_refresh",
            "schedule": crontab(hour=2, minute=0),
        },
    },
)
