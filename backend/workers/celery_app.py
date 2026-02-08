from contextlib import contextmanager

from celery import Celery
from celery.schedules import crontab
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from shared.config import get_settings

settings = get_settings()

celery_app = Celery(
    "imagineai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    # Task routing
    task_routes={
        "workers.tasks.image_processing.*": {"queue": "image_processing"},
        "workers.tasks.classification.*": {"queue": "image_processing"},
        "workers.tasks.feature_extraction.*": {"queue": "image_processing"},
        "workers.tasks.defect_detection.*": {"queue": "image_processing"},
        "workers.tasks.description_gen.*": {"queue": "description_generation"},
        "workers.tasks.batch_processing.*": {"queue": "image_processing"},
        "workers.tasks.notifications.*": {"queue": "notifications"},
        "workers.tasks.webhook_delivery.*": {"queue": "webhooks"},
        "workers.tasks.export_tasks.*": {"queue": "exports"},
    },
    # Task defaults
    task_default_queue="image_processing",
    task_default_exchange="imagineai",
    task_default_routing_key="image.process",
    # Result expiry
    result_expires=3600,
    # Autodiscover
    imports=[
        "workers.tasks.image_processing",
        "workers.tasks.classification",
        "workers.tasks.feature_extraction",
        "workers.tasks.defect_detection",
        "workers.tasks.description_gen",
        "workers.tasks.batch_processing",
        "workers.tasks.notifications",
        "workers.tasks.webhook_delivery",
        "workers.tasks.export_tasks",
    ],
    # Beat schedule
    beat_schedule={
        "cleanup-expired-exports": {
            "task": "workers.tasks.export_tasks.cleanup_expired_exports",
            "schedule": crontab(hour=3, minute=0),
        },
    },
)

# Synchronous session factory for worker tasks
_sync_engine = None
_SyncSessionFactory = None


def _get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    return _sync_engine


@contextmanager
def get_sync_session():
    """Context manager that yields a synchronous SQLAlchemy session for Celery tasks."""
    global _SyncSessionFactory
    if _SyncSessionFactory is None:
        _SyncSessionFactory = sessionmaker(bind=_get_sync_engine())
    session = _SyncSessionFactory()
    try:
        yield session
    finally:
        session.close()
