"""Celery application configuration for Petrix."""
from celery import Celery

from app.config import settings

celery_app = Celery(
    "petrix_workers",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.email_tasks",
        "app.workers.hardening_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
    task_soft_time_limit=1800,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
)
