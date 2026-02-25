import uuid

from fastapi import APIRouter, Depends, Query

from fastapi_app.api.deps import CurrentOrg, CurrentUser, DBSession
from fastapi_app.services.product_service import (
    create_product,
    delete_product,
    get_product,
    list_products,
    update_product,
)
from shared.constants import ProductCategory, ProductStatus
from shared.schemas.analysis import AnalysisResultResponse
from shared.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
    ProductFilter,
)

router = APIRouter()


@router.get("", response_model=ProductListResponse)
async def list_user_products(
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
    category: ProductCategory | None = None,
    status: ProductStatus | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = ProductFilter(
        category=category, status=status, search=search, page=page, page_size=page_size
    )
    return await list_products(db, current_org.id, filters)


@router.post("", response_model=ProductResponse, status_code=201)
async def create_new_product(
    data: ProductCreate,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    return await create_product(db, current_user.id, current_org.id, data)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_detail(
    product_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    return await get_product(db, product_id, current_org.id)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_existing_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    return await update_product(db, product_id, current_org.id, data)


@router.delete("/{product_id}", status_code=204)
async def delete_existing_product(
    product_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    await delete_product(db, product_id, current_org.id)


@router.get("/{product_id}/analysis", response_model=list[AnalysisResultResponse])
async def get_product_analysis(
    product_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
    current_org: CurrentOrg,
):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from shared.models.analysis import AnalysisResult

    product = await get_product(db, product_id, current_org.id)
    image_ids = [img.id for img in product.images]

    if not image_ids:
        return []

    result = await db.execute(
        select(AnalysisResult)
        .options(
            selectinload(AnalysisResult.extracted_attributes),
            selectinload(AnalysisResult.detected_defects),
        )
        .where(AnalysisResult.product_image_id.in_(image_ids))
    )
    return list(result.scalars().all())
