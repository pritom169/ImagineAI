import hashlib
import hmac
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.webhook import WebhookEndpoint


def compute_signature(payload_json: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload_json.encode(), hashlib.sha256).hexdigest()


async def dispatch_webhooks(
    event_type: str, payload: dict, org_id: str, db: AsyncSession
) -> None:
    import uuid

    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.organization_id == uuid.UUID(org_id),
            WebhookEndpoint.is_active.is_(True),
        )
    )
    endpoints = result.scalars().all()

    from workers.tasks.webhook_delivery import deliver_webhook

    for endpoint in endpoints:
        if event_type in endpoint.events:
            deliver_webhook.delay(str(endpoint.id), event_type, payload)
