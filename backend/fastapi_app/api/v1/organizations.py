import uuid

from fastapi import APIRouter, status

from fastapi_app.api.deps import CurrentUser, DBSession
from fastapi_app.services import organization_service
from shared.schemas.organization import (
    InviteMemberRequest,
    OrganizationCreate,
    OrganizationMemberResponse,
    OrganizationResponse,
    OrganizationUpdate,
    UpdateMemberRoleRequest,
)

router = APIRouter()


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> OrganizationResponse:
    org = await organization_service.create_organization(db, current_user.id, data)
    return OrganizationResponse.model_validate(org)


@router.get("/", response_model=list[OrganizationResponse])
async def list_organizations(
    db: DBSession,
    current_user: CurrentUser,
) -> list[OrganizationResponse]:
    orgs = await organization_service.list_user_organizations(db, current_user.id)
    return [OrganizationResponse.model_validate(o) for o in orgs]


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> OrganizationResponse:
    org = await organization_service.get_organization(db, org_id, current_user.id)
    return OrganizationResponse.model_validate(org)


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: uuid.UUID,
    data: OrganizationUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> OrganizationResponse:
    org = await organization_service.update_organization(db, org_id, current_user.id, data)
    return OrganizationResponse.model_validate(org)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> None:
    await organization_service.delete_organization(db, org_id, current_user.id)


@router.get("/{org_id}/members", response_model=list[OrganizationMemberResponse])
async def list_members(
    org_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> list[OrganizationMemberResponse]:
    members = await organization_service.list_members(db, org_id, current_user.id)
    return [OrganizationMemberResponse(**m) for m in members]


@router.post(
    "/{org_id}/members",
    response_model=OrganizationMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_member(
    org_id: uuid.UUID,
    data: InviteMemberRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> OrganizationMemberResponse:
    member = await organization_service.invite_member(
        db, org_id, current_user.id, data.email, data.role
    )
    return OrganizationMemberResponse(**member)


@router.patch("/{org_id}/members/{member_id}", response_model=OrganizationMemberResponse)
async def update_member_role(
    org_id: uuid.UUID,
    member_id: uuid.UUID,
    data: UpdateMemberRoleRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> OrganizationMemberResponse:
    member = await organization_service.update_member_role(
        db, org_id, member_id, current_user.id, data.role
    )
    return OrganizationMemberResponse(**member)


@router.delete("/{org_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: uuid.UUID,
    member_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> None:
    await organization_service.remove_member(db, org_id, member_id, current_user.id)
