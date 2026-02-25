import uuid

from fastapi import APIRouter, status
from sqlalchemy import select

from fastapi_app.api.deps import CurrentOrg, CurrentUser, DBSession
from shared.exceptions import NotFoundError
from shared.models.rate_limit import RateLimitConfig

from pydantic import BaseModel

router = APIRouter()


class RateLimitConfigCreate(BaseModel):
    endpoint_pattern: str = "*"
    requests_per_minute: int = 60
    requests_per_hour: int = 1000


class RateLimitConfigUpdate(BaseModel):
    requests_per_minute: int | None = None
    requests_per_hour: int | None = None
    is_active: bool | None = None


class RateLimitConfigResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID | None
    endpoint_pattern: str
    requests_per_minute: int
    requests_per_hour: int
    is_active: bool

    model_config = {"from_attributes": True}


@router.post("/", response_model=RateLimitConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_rate_limit(
    data: RateLimitConfigCreate,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    config = RateLimitConfig(
        organization_id=current_org.id,
        endpoint_pattern=data.endpoint_pattern,
        requests_per_minute=data.requests_per_minute,
        requests_per_hour=data.requests_per_hour,
    )
    db.add(config)
    await db.flush()
    await db.refresh(config)
    return config


@router.get("/", response_model=list[RateLimitConfigResponse])
async def list_rate_limits(
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    result = await db.execute(
        select(RateLimitConfig).where(
            RateLimitConfig.organization_id == current_org.id
        )
    )
    return list(result.scalars().all())


@router.patch("/{config_id}", response_model=RateLimitConfigResponse)
async def update_rate_limit(
    config_id: uuid.UUID,
    data: RateLimitConfigUpdate,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    result = await db.execute(
        select(RateLimitConfig).where(
            RateLimitConfig.id == config_id,
            RateLimitConfig.organization_id == current_org.id,
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise NotFoundError("Rate limit config", str(config_id))

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    await db.flush()
    await db.refresh(config)
    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate_limit(
    config_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    result = await db.execute(
        select(RateLimitConfig).where(
            RateLimitConfig.id == config_id,
            RateLimitConfig.organization_id == current_org.id,
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise NotFoundError("Rate limit config", str(config_id))
    await db.delete(config)
    await db.flush()
