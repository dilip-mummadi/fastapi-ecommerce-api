"""Product review endpoints."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewRead
from app.services import review_service

router = APIRouter(tags=["reviews"])


@router.get("/products/{product_id}/reviews", response_model=list[ReviewRead])
async def list_reviews(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await review_service.list_reviews_for_product(db, product_id)


@router.post("/products/{product_id}/reviews", response_model=ReviewRead, status_code=201)
async def create_review(
    product_id: uuid.UUID,
    review_in: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await review_service.create_review(db, product_id, current_user.id, review_in)


@router.delete("/reviews/{review_id}", status_code=204)
async def delete_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await review_service.delete_review(db, review_id, current_user.id)
