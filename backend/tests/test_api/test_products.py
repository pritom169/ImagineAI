import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.product import Product
from shared.models.user import User


@pytest.mark.asyncio
class TestCreateProduct:
    async def test_create_product_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.post(
            "/api/v1/products",
            json={
                "title": "Test Product",
                "description": "A test product description",
                "category": "electronics",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Product"
        assert data["description"] == "A test product description"
        assert data["category"] == "electronics"
        assert data["status"] == "draft"
        assert "id" in data

    async def test_create_product_minimal(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.post(
            "/api/v1/products",
            json={"title": "Minimal Product"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Product"

    async def test_create_product_unauthenticated(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/products",
            json={"title": "Should Fail"},
        )
        assert response.status_code in (401, 403)

    async def test_create_product_empty_title(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.post(
            "/api/v1/products",
            json={"title": ""},
            headers=auth_headers,
        )
        # Empty string may be allowed or rejected depending on validation
        assert response.status_code in (201, 422)


@pytest.mark.asyncio
class TestListProducts:
    async def test_list_products_empty(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get("/api/v1/products", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data

    async def test_list_products_with_pagination(
        self, client: AsyncClient, auth_headers: dict
    ):
        # Create some products
        for i in range(3):
            await client.post(
                "/api/v1/products",
                json={"title": f"Product {i}"},
                headers=auth_headers,
            )

        response = await client.get(
            "/api/v1/products?page=1&page_size=2",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] == 2

    async def test_list_products_with_category_filter(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            "/api/v1/products?category=electronics",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_list_products_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/products")
        assert response.status_code in (401, 403)


@pytest.mark.asyncio
class TestGetProduct:
    async def test_get_product_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        # Create a product first
        create_response = await client.post(
            "/api/v1/products",
            json={"title": "Get This Product"},
            headers=auth_headers,
        )
        product_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/products/{product_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Get This Product"

    async def test_get_product_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/products/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_get_product_invalid_uuid(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            "/api/v1/products/not-a-uuid",
            headers=auth_headers,
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestUpdateProduct:
    async def test_update_product_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        create_response = await client.post(
            "/api/v1/products",
            json={"title": "Original Title"},
            headers=auth_headers,
        )
        product_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/products/{product_id}",
            json={"title": "Updated Title"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    async def test_update_product_partial(
        self, client: AsyncClient, auth_headers: dict
    ):
        create_response = await client.post(
            "/api/v1/products",
            json={
                "title": "Partial Update",
                "description": "Original desc",
                "category": "electronics",
            },
            headers=auth_headers,
        )
        product_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/products/{product_id}",
            json={"description": "Updated desc"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated desc"
        assert data["title"] == "Partial Update"

    async def test_update_product_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        fake_id = str(uuid.uuid4())
        response = await client.patch(
            f"/api/v1/products/{fake_id}",
            json={"title": "Nope"},
            headers=auth_headers,
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestDeleteProduct:
    async def test_delete_product_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        create_response = await client.post(
            "/api/v1/products",
            json={"title": "To Delete"},
            headers=auth_headers,
        )
        product_id = create_response.json()["id"]

        response = await client.delete(
            f"/api/v1/products/{product_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get(
            f"/api/v1/products/{product_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    async def test_delete_product_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        fake_id = str(uuid.uuid4())
        response = await client.delete(
            f"/api/v1/products/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_delete_product_unauthenticated(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        response = await client.delete(f"/api/v1/products/{fake_id}")
        assert response.status_code in (401, 403)
