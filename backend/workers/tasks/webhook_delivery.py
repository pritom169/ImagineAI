import hashlib
import hmac
import json
import uuid
from datetime import datetime, UTC

import httpx
from celery import shared_task

from shared.config import get_settings
from workers.celery_app import get_sync_session

settings = get_settings()


@shared_task(
    bind=True,
    max_retries=5,
    acks_late=True,
    time_limit=30,
    soft_time_limit=25,
)
def deliver_webhook(self, endpoint_id: str, event_type: str, payload: dict):
    from shared.models.webhook import WebhookDelivery, WebhookEndpoint

    with get_sync_session() as session:
        endpoint = session.get(WebhookEndpoint, uuid.UUID(endpoint_id))
        if not endpoint or not endpoint.is_active:
            return

        payload_json = json.dumps(payload, default=str)
        signature = hmac.new(
            endpoint.secret.encode(), payload_json.encode(), hashlib.sha256
        ).hexdigest()

        delivery = WebhookDelivery(
            webhook_id=endpoint.id,
            event_type=event_type,
            payload=payload,
            attempt=self.request.retries + 1,
        )

        try:
            response = httpx.post(
                endpoint.url,
                content=payload_json,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": f"sha256={signature}",
                    "X-Webhook-Event": event_type,
                    "X-Webhook-Delivery-ID": str(delivery.id),
                },
                timeout=10.0,
            )

            delivery.response_status = response.status_code
            delivery.response_body = response.text[:2000]
            delivery.delivered_at = datetime.now(UTC)
            delivery.success = 200 <= response.status_code < 300

            if delivery.success:
                endpoint.failure_count = 0
            else:
                endpoint.failure_count += 1

        except Exception as exc:
            delivery.error_message = str(exc)[:500]
            delivery.success = False
            endpoint.failure_count += 1

        endpoint.last_triggered_at = datetime.now(UTC)
        session.add(delivery)

        # Auto-disable after 10 consecutive failures
        if endpoint.failure_count >= 10:
            endpoint.is_active = False

        session.commit()

        if not delivery.success and self.request.retries < self.max_retries:
            backoff = 2 ** self.request.retries * 30
            raise self.retry(countdown=backoff)
