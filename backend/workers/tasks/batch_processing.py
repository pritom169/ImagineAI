import logging
from datetime import UTC, datetime

from celery import group, shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from shared.config import get_settings
from shared.constants import JobStatus
from shared.models.pipeline import ProcessingJob
from workers.tasks.image_processing import process_image

logger = logging.getLogger(__name__)
settings = get_settings()

sync_engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
SyncSession = sessionmaker(bind=sync_engine)


@shared_task(
    bind=True,
    max_retries=1,
    acks_late=True,
    time_limit=1800,
    soft_time_limit=1750,
)
def process_batch(self, job_id: str, image_ids: list[str]):
    """Orchestrate batch processing by fanning out individual image tasks."""
    logger.info(f"Starting batch processing job={job_id}, images={len(image_ids)}")

    with SyncSession() as session:
        job = session.execute(
            select(ProcessingJob).where(ProcessingJob.id == job_id)
        ).scalar_one()
        job.status = JobStatus.PROCESSING.value
        job.started_at = datetime.now(UTC)
        session.commit()

    # Fan out individual tasks using a Celery group
    batch = group(process_image.s(image_id, job_id) for image_id in image_ids)
    result = batch.apply_async()

    # Store the group result ID
    with SyncSession() as session:
        job = session.execute(
            select(ProcessingJob).where(ProcessingJob.id == job_id)
        ).scalar_one()
        job.metadata_ = {**(job.metadata_ or {}), "group_id": result.id}
        session.commit()

    logger.info(f"Dispatched {len(image_ids)} tasks for batch job={job_id}")
