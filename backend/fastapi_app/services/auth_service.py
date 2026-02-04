from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import get_settings
from shared.exceptions import AuthenticationError, ConflictError
from shared.models.user import User
from shared.schemas.auth import TokenPair, UserCreate

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(user_id: str, token_type: str, expires_delta: timedelta) -> str:
    expire = datetime.now(UTC) + expires_delta
    payload = {"sub": user_id, "type": token_type, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_token_pair(user_id: str) -> TokenPair:
    access_token = create_token(
        user_id,
        "access",
        timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )
    refresh_token = create_token(
        user_id,
        "refresh",
        timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


async def register_user(db: AsyncSession, user_data: UserCreate) -> User:
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise ConflictError("A user with this email already exists")

    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise AuthenticationError("Invalid email or password")
    if not user.is_active:
        raise AuthenticationError("Account is disabled")

    user.last_login = datetime.now(UTC)
    await db.flush()
    return user


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenPair:
    from jose import JWTError

    try:
        payload = jwt.decode(
            refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")
        user_id = payload.get("sub")
    except JWTError:
        raise AuthenticationError("Invalid refresh token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise AuthenticationError("User not found or disabled")

    return create_token_pair(str(user.id))
