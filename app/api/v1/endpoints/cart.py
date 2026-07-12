"""Shopping cart endpoints, scoped to the authenticated user."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartRead
from app.services import cart_service

router = APIRouter(tags=["cart"])


@router.get("/", response_model=CartRead)
async def get_cart(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return await cart_service.get_cart(db, current_user.id)


@router.post("/items", response_model=CartRead, status_code=201)
async def add_item(
    item_in: CartItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await cart_service.add_item(db, current_user.id, item_in)


@router.patch("/items/{item_id}", response_model=CartRead)
async def update_item(
    item_id: uuid.UUID,
    item_in: CartItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await cart_service.update_item(db, current_user.id, item_id, item_in)


@router.delete("/items/{item_id}", response_model=CartRead)
async def remove_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await cart_service.remove_item(db, current_user.id, item_id)
