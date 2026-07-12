"""Business logic for products: CRUD, search/filter/pagination, rating aggregation."""
import math
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.models.product import Product
from app.models.review import Review
from app.schemas.category import CategoryRead
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.category_service import slugify


def _to_read_model(product: Product, avg_rating: float | None, review_count: int) -> ProductRead:
    return ProductRead(
        id=product.id,
        name=product.name,
        slug=product.slug,
        description=product.description,
        price=product.price,
        stock=product.stock,
        image_url=product.image_url,
        is_active=product.is_active,
        category=CategoryRead.model_validate(product.category) if product.category else None,
        created_at=product.created_at,
        avg_rating=round(avg_rating, 2) if avg_rating else None,
        review_count=review_count,
    )


async def _with_rating(db: AsyncSession, product: Product) -> ProductRead:
    result = await db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(Review.product_id == product.id)
    )
    avg_rating, review_count = result.one()
    return _to_read_model(product, avg_rating, review_count or 0)


async def create_product(db: AsyncSession, product_in: ProductCreate) -> ProductRead:
    slug = slugify(product_in.name)
    existing = await db.execute(select(Product).where(Product.slug == slug))
    if existing.scalar_one_or_none():
        raise ConflictError(f"Product '{product_in.name}' already exists")

    product = Product(**product_in.model_dump(), slug=slug)
    db.add(product)
    await db.commit()
    await db.refresh(product, attribute_names=["category"])
    return await _with_rating(db, product)


async def get_product(db: AsyncSession, product_id: uuid.UUID) -> Product:
    result = await db.execute(
        select(Product).options(selectinload(Product.category)).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise NotFoundError("Product not found")
    return product


async def get_product_read(db: AsyncSession, product_id: uuid.UUID) -> ProductRead:
    product = await get_product(db, product_id)
    return await _with_rating(db, product)


async def list_products(
    db: AsyncSession,
    *,
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    category_id: uuid.UUID | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort: str = "created_at",
) -> tuple[list[ProductRead], int]:
    query = select(Product).options(selectinload(Product.category)).where(Product.is_active.is_(True))

    if search:
        like = f"%{search}%"
        query = query.where(Product.name.ilike(like) | Product.description.ilike(like))
    if category_id:
        query = query.where(Product.category_id == category_id)
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)

    sort_map = {
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "name": Product.name.asc(),
        "created_at": Product.created_at.desc(),
    }
    query = query.order_by(sort_map.get(sort, Product.created_at.desc()))

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    products = list(result.scalars().all())

    reads = [await _with_rating(db, p) for p in products]
    return reads, total


async def update_product(db: AsyncSession, product_id: uuid.UUID, product_in: ProductUpdate) -> ProductRead:
    product = await get_product(db, product_id)
    for field, value in product_in.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await db.commit()
    await db.refresh(product, attribute_names=["category"])
    return await _with_rating(db, product)


async def delete_product(db: AsyncSession, product_id: uuid.UUID) -> None:
    product = await get_product(db, product_id)
    product.is_active = False  # soft delete: preserves order history integrity
    await db.commit()


def total_pages(total: int, size: int) -> int:
    return max(1, math.ceil(total / size))
