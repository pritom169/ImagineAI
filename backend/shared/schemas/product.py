import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from shared.constants import ProductCategory, ProductStatus


class ProductCreate(BaseModel):
    title: str = Field(max_length=500)
    description: str | None = None
    category: ProductCategory | None = None


class ProductUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    description: str | None = None
    category: ProductCategory | None = None
    status: ProductStatus | None = None


class ProductImageResponse(BaseModel):
    id: uuid.UUID
    s3_key: str
    original_filename: str | None
    content_type: str | None
    file_size_bytes: int | None
    width: int | None
    height: int | None
    is_primary: bool
    upload_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID
    title: str | None
    description: str | None
    category: str | None
    subcategory: str | None
    ai_description: str | None
    status: str
    metadata_: dict = Field(alias="metadata_")
    images: list[ProductImageResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ProductFilter(BaseModel):
    category: ProductCategory | None = None
    status: ProductStatus | None = None
    search: str | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
