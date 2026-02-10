import asyncio
import uuid
from collections.abc import AsyncGenerator
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.models import Base
from shared.models.user import User
from fastapi_app.services.auth_service import create_token_pair, hash_password

# Use an in-memory SQLite for tests or a test PostgreSQL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"test-{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict[str, str]:
    tokens = create_token_pair(str(test_user.id))
    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    from fastapi_app.main import app
    from fastapi_app.api.deps import get_current_user
    from shared.database import get_db_session

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_db

    # Mock Redis
    mock_redis = MagicMock()
    mock_redis.ping = MagicMock(return_value=True)
    mock_redis.close = MagicMock(return_value=asyncio.coroutine(lambda: None)())
    app.state.redis = mock_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_s3():
    with patch("fastapi_app.services.upload_service.get_s3_client") as mock:
        s3_client = MagicMock()
        s3_client.generate_presigned_url.return_value = "https://s3.example.com/presigned"
        s3_client.head_object.return_value = {}
        s3_client.put_object.return_value = {}
        mock.return_value = s3_client
        yield s3_client


@pytest.fixture
def mock_celery():
    with patch("workers.tasks.image_processing.process_image") as mock:
        mock.delay.return_value = MagicMock(id="test-task-id")
        yield mock
