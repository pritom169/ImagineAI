import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User


@pytest.mark.asyncio
class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepass123",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    async def test_register_short_password(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "short@example.com",
                "password": "short",
            },
        )
        assert response.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "securepass123",
            },
        )
        assert response.status_code == 422

    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "securepass123",
            },
        )
        assert response.status_code in (400, 409)

    async def test_register_missing_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={"password": "securepass123"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client: AsyncClient, test_user: User):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code in (401, 400)

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "somepassword123",
            },
        )
        assert response.status_code in (401, 400, 404)

    async def test_login_missing_fields(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422


@pytest.mark.asyncio
class TestTokenRefresh:
    async def test_refresh_token(self, client: AsyncClient, test_user: User):
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        if login_response.status_code != 200:
            pytest.skip("Login failed, cannot test refresh")

        tokens = login_response.json()
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_invalid_token(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code in (401, 400)


@pytest.mark.asyncio
class TestGetMe:
    async def test_get_me_authenticated(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == str(test_user.id)

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)

    async def test_get_me_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code in (401, 403)
