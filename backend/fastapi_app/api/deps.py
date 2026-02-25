import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import get_settings
from shared.database import get_db_session
from shared.exceptions import AuthorizationError
from shared.models.organization import Organization, OrganizationMember
from shared.models.user import User

settings = get_settings()
security = HTTPBearer()

DBSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: DBSession,
) -> User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if user_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_org(
    db: DBSession,
    current_user: CurrentUser,
    x_organization_id: uuid.UUID = Header(),
) -> Organization:
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == x_organization_id,
            OrganizationMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise AuthorizationError("Not a member of this organization")

    org_result = await db.execute(
        select(Organization).where(
            Organization.id == x_organization_id, Organization.is_active.is_(True)
        )
    )
    org = org_result.scalar_one_or_none()
    if not org:
        raise AuthorizationError("Organization not found or inactive")
    return org


CurrentOrg = Annotated[Organization, Depends(get_current_org)]
