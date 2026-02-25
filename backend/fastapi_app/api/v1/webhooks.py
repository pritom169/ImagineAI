import secrets
import uuid

from fastapi import APIRouter, Query, status
from sqlalchemy import select

from fastapi_app.api.deps import CurrentOrg, CurrentUser, DBSession
from shared.exceptions import NotFoundError
from shared.models.webhook import WebhookDelivery, WebhookEndpoint
from shared.schemas.webhook import (
    WebhookCreate,
    WebhookDeliveryResponse,
    WebhookResponse,
    WebhookUpdate,
)

router = APIRouter()


@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: WebhookCreate,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    webhook = WebhookEndpoint(
        organization_id=current_org.id,
        url=data.url,
        secret=secrets.token_hex(32),
        events=data.events,
        description=data.description,
    )
    db.add(webhook)
    await db.flush()
    await db.refresh(webhook)
    return webhook


@router.get("/", response_model=list[WebhookResponse])
async def list_webhooks(
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    result = await db.execute(
        select(WebhookEndpoint)
        .where(WebhookEndpoint.organization_id == current_org.id)
        .order_by(WebhookEndpoint.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.organization_id == current_org.id,
        )
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise NotFoundError("Webhook", str(webhook_id))
    return webhook


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: uuid.UUID,
    data: WebhookUpdate,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.organization_id == current_org.id,
        )
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise NotFoundError("Webhook", str(webhook_id))

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(webhook, field, value)
    await db.flush()
    await db.refresh(webhook)
    return webhook


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.organization_id == current_org.id,
        )
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise NotFoundError("Webhook", str(webhook_id))
    await db.delete(webhook)
    await db.flush()


@router.post("/{webhook_id}/test", response_model=dict)
async def test_webhook(
    webhook_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.organization_id == current_org.id,
        )
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise NotFoundError("Webhook", str(webhook_id))

    from workers.tasks.webhook_delivery import deliver_webhook

    deliver_webhook.delay(
        str(webhook.id), "test.ping", {"message": "Test webhook delivery"}
    )
    return {"status": "queued", "message": "Test webhook delivery queued"}


@router.get("/{webhook_id}/deliveries", response_model=list[WebhookDeliveryResponse])
async def list_deliveries(
    webhook_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    # Verify webhook belongs to org
    wh_result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_id,
            WebhookEndpoint.organization_id == current_org.id,
        )
    )
    if not wh_result.scalar_one_or_none():
        raise NotFoundError("Webhook", str(webhook_id))

    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())
