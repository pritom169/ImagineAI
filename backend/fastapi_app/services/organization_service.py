import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.constants import OrgRole
from shared.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationError
from shared.models.organization import Organization, OrganizationMember
from shared.models.user import User
from shared.schemas.organization import OrganizationCreate, OrganizationUpdate


ROLE_HIERARCHY = {
    OrgRole.OWNER: 4,
    OrgRole.ADMIN: 3,
    OrgRole.MEMBER: 2,
    OrgRole.VIEWER: 1,
}


def check_role(member: OrganizationMember, min_role: OrgRole) -> None:
    if ROLE_HIERARCHY.get(OrgRole(member.role), 0) < ROLE_HIERARCHY[min_role]:
        raise AuthorizationError("Insufficient organization permissions")


async def create_organization(
    db: AsyncSession, user_id: uuid.UUID, data: OrganizationCreate
) -> Organization:
    existing = await db.execute(
        select(Organization).where(Organization.slug == data.slug)
    )
    if existing.scalar_one_or_none():
        raise ConflictError(f"Organization with slug '{data.slug}' already exists")

    org = Organization(name=data.name, slug=data.slug)
    db.add(org)
    await db.flush()

    membership = OrganizationMember(
        organization_id=org.id, user_id=user_id, role=OrgRole.OWNER.value
    )
    db.add(membership)
    await db.flush()
    await db.refresh(org)
    return org


async def list_user_organizations(db: AsyncSession, user_id: uuid.UUID) -> list[Organization]:
    result = await db.execute(
        select(Organization)
        .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
        .where(OrganizationMember.user_id == user_id, Organization.is_active.is_(True))
        .order_by(Organization.name)
    )
    return list(result.scalars().all())


async def get_organization(
    db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID
) -> Organization:
    result = await db.execute(
        select(Organization).where(Organization.id == org_id, Organization.is_active.is_(True))
    )
    org = result.scalar_one_or_none()
    if not org:
        raise NotFoundError("Organization", str(org_id))

    await _verify_membership(db, org_id, user_id)
    return org


async def update_organization(
    db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID, data: OrganizationUpdate
) -> Organization:
    org = await get_organization(db, org_id, user_id)
    member = await _get_membership(db, org_id, user_id)
    check_role(member, OrgRole.ADMIN)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)
    await db.flush()
    await db.refresh(org)
    return org


async def delete_organization(
    db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    org = await get_organization(db, org_id, user_id)
    member = await _get_membership(db, org_id, user_id)
    check_role(member, OrgRole.OWNER)

    org.is_active = False
    await db.flush()


async def list_members(
    db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID
) -> list[dict]:
    await _verify_membership(db, org_id, user_id)

    result = await db.execute(
        select(OrganizationMember)
        .options(selectinload(OrganizationMember.user))
        .where(OrganizationMember.organization_id == org_id)
        .order_by(OrganizationMember.created_at)
    )
    members = result.scalars().all()
    return [
        {
            "id": m.id,
            "user_id": m.user_id,
            "email": m.user.email,
            "full_name": m.user.full_name,
            "role": m.role,
            "created_at": m.created_at,
        }
        for m in members
    ]


async def invite_member(
    db: AsyncSession, org_id: uuid.UUID, inviter_id: uuid.UUID, email: str, role: str
) -> dict:
    inviter_member = await _get_membership(db, org_id, inviter_id)
    check_role(inviter_member, OrgRole.ADMIN)

    if role not in [r.value for r in OrgRole]:
        raise ValidationError(f"Invalid role: {role}")
    if role == OrgRole.OWNER.value:
        raise AuthorizationError("Cannot assign owner role via invite")

    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", email)

    existing = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError(f"User '{email}' is already a member")

    membership = OrganizationMember(
        organization_id=org_id, user_id=user.id, role=role
    )
    db.add(membership)
    await db.flush()
    await db.refresh(membership)

    return {
        "id": membership.id,
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": membership.role,
        "created_at": membership.created_at,
    }


async def update_member_role(
    db: AsyncSession, org_id: uuid.UUID, member_id: uuid.UUID, updater_id: uuid.UUID, role: str
) -> dict:
    updater_member = await _get_membership(db, org_id, updater_id)
    check_role(updater_member, OrgRole.ADMIN)

    result = await db.execute(
        select(OrganizationMember)
        .options(selectinload(OrganizationMember.user))
        .where(OrganizationMember.id == member_id, OrganizationMember.organization_id == org_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise NotFoundError("Member", str(member_id))

    if member.role == OrgRole.OWNER.value:
        raise AuthorizationError("Cannot change the owner's role")
    if role == OrgRole.OWNER.value:
        raise AuthorizationError("Cannot assign owner role")

    member.role = role
    await db.flush()

    return {
        "id": member.id,
        "user_id": member.user_id,
        "email": member.user.email,
        "full_name": member.user.full_name,
        "role": member.role,
        "created_at": member.created_at,
    }


async def remove_member(
    db: AsyncSession, org_id: uuid.UUID, member_id: uuid.UUID, remover_id: uuid.UUID
) -> None:
    remover_member = await _get_membership(db, org_id, remover_id)
    check_role(remover_member, OrgRole.ADMIN)

    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == org_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise NotFoundError("Member", str(member_id))

    if member.role == OrgRole.OWNER.value:
        raise AuthorizationError("Cannot remove the organization owner")

    await db.delete(member)
    await db.flush()


async def _get_membership(
    db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID
) -> OrganizationMember:
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise AuthorizationError("Not a member of this organization")
    return member


async def _verify_membership(
    db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    await _get_membership(db, org_id, user_id)
