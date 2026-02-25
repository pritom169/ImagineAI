import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class OrganizationCreate(BaseModel):
    name: str = Field(max_length=255)
    slug: str = Field(max_length=100, pattern=r"^[a-z0-9-]+$")


class OrganizationUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    plan: str | None = None


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    plan: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrganizationMemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    full_name: str | None
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = "member"


class UpdateMemberRoleRequest(BaseModel):
    role: str
