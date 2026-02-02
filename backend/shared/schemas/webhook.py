import uuid
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class WebhookCreate(BaseModel):
    url: str = Field(max_length=2048)
    events: list[str] = Field(min_length=1)
    description: str | None = Field(None, max_length=500)


class WebhookUpdate(BaseModel):
    url: str | None = Field(None, max_length=2048)
    events: list[str] | None = None
    description: str | None = Field(None, max_length=500)
    is_active: bool | None = None


class WebhookResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    url: str
    is_active: bool
    events: list[str]
    description: str | None
    failure_count: int
    last_triggered_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookDeliveryResponse(BaseModel):
    id: uuid.UUID
    webhook_id: uuid.UUID
    event_type: str
    payload: dict
    response_status: int | None
    success: bool
    attempt: int
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
