"""Product catalog endpoints: public search/browse, admin-only writes.

GET /products is cached in Redis for a short TTL since catalog browsing is
the highest-traffic, most repeatable read in a commerce API. Cache is
invalidated on any write.
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user
from app.core.cache import cache_get, cache_invalidate_prefix, cache_set
from app.db.session import get_db
from app.schemas.common import Page
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services import product_service

router = APIRouter(tags=["products"])

CACHE_PREFIX = "products:list:"


@router.get("/", response_model=Page[ProductRead])
async def list_products(
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of items per page (max 100)"),
    search: str | None = None,
    category_id: uuid.UUID | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    sort: str = Query(default="created_at", pattern="^(created_at|price_asc|price_desc|name|rating)$"),
    min_rating: float | None = Query(default=None, ge=0, le=5, description="Filter by minimum average rating"),
):
    cache_key = f"{CACHE_PREFIX}{page}:{page_size}:{search}:{category_id}:{min_price}:{max_price}:{sort}:{min_rating}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    products, total = await product_service.list_products(
        db,
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        min_rating=min_rating,
    )
    page_result = Page(
        items=products,
        total=total,
        page=page,
        page_size=page_size,
        pages=product_service.total_pages(total, page_size),
    )
    await cache_set(cache_key, page_result.model_dump(mode="json"), ttl_seconds=30)
    return page_result


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await product_service.get_product_read(db, product_id)


@router.post(
    "/", response_model=ProductRead, status_code=201, dependencies=[Depends(get_current_admin_user)]
)
async def create_product(product_in: ProductCreate, db: AsyncSession = Depends(get_db)):
    product = await product_service.create_product(db, product_in)
    await cache_invalidate_prefix(CACHE_PREFIX)
    return product


@router.patch(
    "/{product_id}", response_model=ProductRead, dependencies=[Depends(get_current_admin_user)]
)
async def update_product(
    product_id: uuid.UUID, product_in: ProductUpdate, db: AsyncSession = Depends(get_db)
):
    product = await product_service.update_product(db, product_id, product_in)
    await cache_invalidate_prefix(CACHE_PREFIX)
    return product


@router.delete("/{product_id}", status_code=204, dependencies=[Depends(get_current_admin_user)])
async def delete_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await product_service.delete_product(db, product_id)
    await cache_invalidate_prefix(CACHE_PREFIX)
