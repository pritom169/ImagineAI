import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoints:
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_readiness_check_healthy(self, client: AsyncClient):
        response = await client.get("/ready")
        assert response.status_code in (200, 503)
        data = response.json()
        assert "status" in data
        assert "checks" in data

    async def test_health_returns_json(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.headers["content-type"] == "application/json"
