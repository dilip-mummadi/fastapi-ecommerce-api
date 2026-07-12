"""Business logic for categories."""
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.models.category import Category
from app.schemas.category import CategoryCreate


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


async def list_categories(db: AsyncSession) -> list[Category]:
    result = await db.execute(select(Category).order_by(Category.name))
    return list(result.scalars().all())


async def create_category(db: AsyncSession, category_in: CategoryCreate) -> Category:
    slug = slugify(category_in.name)
    existing = await db.execute(select(Category).where(Category.slug == slug))
    if existing.scalar_one_or_none():
        raise ConflictError(f"Category '{category_in.name}' already exists")

    category = Category(name=category_in.name, slug=slug)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category
