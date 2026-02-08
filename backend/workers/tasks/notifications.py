import json
import logging
from datetime import UTC, datetime

import redis

from shared.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def get_sync_redis():
    return redis.from_url(settings.redis_url, decode_responses=True)


def publish_step_update(
    job_id: str,
    image_id: str | None,
    step: str,
    status: str,
    progress: dict | None = None,
    data: dict | None = None,
):
    """Publish a processing step update to Redis pub/sub."""
    message = {
        "type": "step_update",
        "job_id": job_id,
        "image_id": image_id,
        "step": step,
        "status": status,
        "progress": progress,
        "data": data,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    r = get_sync_redis()
    r.publish(f"job:{job_id}", json.dumps(message))
    r.close()


def publish_job_complete(job_id: str, progress: dict | None = None):
    """Publish a job completion event."""
    message = {
        "type": "job_complete",
        "job_id": job_id,
        "status": "completed",
        "progress": progress,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    r = get_sync_redis()
    r.publish(f"job:{job_id}", json.dumps(message))
    r.close()

    # Dispatch webhooks for job completion
    _dispatch_job_webhooks(job_id, "job.completed", progress)


def publish_job_failed(job_id: str, error: str):
    """Publish a job failure event."""
    message = {
        "type": "job_failed",
        "job_id": job_id,
        "status": "failed",
        "data": {"error": error},
        "timestamp": datetime.now(UTC).isoformat(),
    }
    r = get_sync_redis()
    r.publish(f"job:{job_id}", json.dumps(message))
    r.close()

    # Dispatch webhooks for job failure
    _dispatch_job_webhooks(job_id, "job.failed", {"error": error})


def _dispatch_job_webhooks(job_id: str, event_type: str, data: dict | None = None):
    """Look up the org for a job and dispatch webhooks."""
    try:
        from sqlalchemy import select

        from shared.models.pipeline import ProcessingJob
        from shared.models.product import Product, ProductImage
        from shared.models.webhook import WebhookEndpoint
        from workers.celery_app import get_sync_session
        from workers.tasks.webhook_delivery import deliver_webhook

        with get_sync_session() as session:
            job = session.execute(
                select(ProcessingJob).where(ProcessingJob.id == job_id)
            ).scalar_one_or_none()
            if not job:
                return

            # Find org via the first image's product
            image = session.execute(
                select(ProductImage).where(ProductImage.id == job.product_image_ids[0])
            ).scalar_one_or_none() if job.product_image_ids else None

            if not image:
                return

            product = session.execute(
                select(Product).where(Product.id == image.product_id)
            ).scalar_one_or_none()
            if not product or not product.organization_id:
                return

            org_id = product.organization_id

            # Find active webhooks that subscribe to this event
            webhooks = session.execute(
                select(WebhookEndpoint).where(
                    WebhookEndpoint.organization_id == org_id,
                    WebhookEndpoint.is_active.is_(True),
                )
            ).scalars().all()

            payload = {
                "event": event_type,
                "job_id": str(job_id),
                "timestamp": datetime.now(UTC).isoformat(),
                **(data or {}),
            }

            for webhook in webhooks:
                if event_type in webhook.events or "*" in webhook.events:
                    deliver_webhook.delay(str(webhook.id), event_type, payload)

    except Exception:
        logger.warning(f"Failed to dispatch webhooks for job {job_id}", exc_info=True)
