"""Business logic for product reviews."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.review import Review
from app.schemas.review import ReviewCreate


async def list_reviews_for_product(db: AsyncSession, product_id: uuid.UUID) -> list[Review]:
    result = await db.execute(
        select(Review).where(Review.product_id == product_id).order_by(Review.created_at.desc())
    )
    return list(result.scalars().all())


async def create_review(
    db: AsyncSession, product_id: uuid.UUID, user_id: uuid.UUID, review_in: ReviewCreate
) -> Review:
    existing = await db.execute(
        select(Review).where(Review.product_id == product_id, Review.user_id == user_id)
    )
    if existing.scalar_one_or_none():
        raise ConflictError("You already reviewed this product")

    review = Review(product_id=product_id, user_id=user_id, **review_in.model_dump())
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


async def delete_review(db: AsyncSession, review_id: uuid.UUID, user_id: uuid.UUID) -> None:
    result = await db.execute(
        select(Review).where(Review.id == review_id, Review.user_id == user_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise NotFoundError("Review not found")
    await db.delete(review)
    await db.commit()
