from fastapi import APIRouter

from fastapi_app.api.deps import CurrentUser, DBSession
from fastapi_app.services.auth_service import (
    authenticate_user,
    create_token_pair,
    refresh_access_token,
    register_user,
)
from shared.schemas.auth import (
    TokenPair,
    TokenRefresh,
    UserCreate,
    UserLogin,
    UserResponse,
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user_data: UserCreate, db: DBSession):
    user = await register_user(db, user_data)
    return user


@router.post("/login", response_model=TokenPair)
async def login(credentials: UserLogin, db: DBSession):
    user = await authenticate_user(db, credentials.email, credentials.password)
    return create_token_pair(str(user.id))


@router.post("/refresh", response_model=TokenPair)
async def refresh(body: TokenRefresh, db: DBSession):
    return await refresh_access_token(db, body.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    return current_user
