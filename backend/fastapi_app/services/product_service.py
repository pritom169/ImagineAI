import math
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.exceptions import NotFoundError
from shared.models.product import Product
from shared.schemas.product import ProductCreate, ProductFilter, ProductUpdate


async def create_product(
    db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID, data: ProductCreate
) -> Product:
    product = Product(
        user_id=user_id,
        organization_id=org_id,
        title=data.title,
        description=data.description,
        category=data.category.value if data.category else None,
    )
    db.add(product)
    await db.flush()
    await db.refresh(product, attribute_names=["images"])
    return product


async def get_product(
    db: AsyncSession, product_id: uuid.UUID, org_id: uuid.UUID
) -> Product:
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.images))
        .where(Product.id == product_id, Product.organization_id == org_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError("Product", str(product_id))
    return product


async def list_products(
    db: AsyncSession, org_id: uuid.UUID, filters: ProductFilter
) -> dict:
    query = select(Product).where(Product.organization_id == org_id)
    count_query = select(func.count(Product.id)).where(Product.organization_id == org_id)

    if filters.category:
        query = query.where(Product.category == filters.category.value)
        count_query = count_query.where(Product.category == filters.category.value)
    if filters.status:
        query = query.where(Product.status == filters.status.value)
        count_query = count_query.where(Product.status == filters.status.value)
    if filters.search:
        search_term = f"%{filters.search}%"
        query = query.where(Product.title.ilike(search_term))
        count_query = count_query.where(Product.title.ilike(search_term))

    total = (await db.execute(count_query)).scalar() or 0
    offset = (filters.page - 1) * filters.page_size

    query = (
        query.options(selectinload(Product.images))
        .order_by(Product.created_at.desc())
        .offset(offset)
        .limit(filters.page_size)
    )
    result = await db.execute(query)
    items = list(result.scalars().all())

    return {
        "items": items,
        "total": total,
        "page": filters.page,
        "page_size": filters.page_size,
        "pages": math.ceil(total / filters.page_size) if total > 0 else 0,
    }


async def update_product(
    db: AsyncSession, product_id: uuid.UUID, org_id: uuid.UUID, data: ProductUpdate
) -> Product:
    product = await get_product(db, product_id, org_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(product, field, value)
    await db.flush()
    await db.refresh(product, attribute_names=["images"])
    return product


async def delete_product(
    db: AsyncSession, product_id: uuid.UUID, org_id: uuid.UUID
) -> None:
    product = await get_product(db, product_id, org_id)
    await db.delete(product)
    await db.flush()
