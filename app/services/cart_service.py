"""Business logic for the shopping cart."""
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import InsufficientStockError, NotFoundError
from app.models.cart import Cart, CartItem
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartRead
from app.services.product_service import get_product


async def _get_or_create_cart(db: AsyncSession, user_id: uuid.UUID) -> Cart:
    result = await db.execute(
        select(Cart)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
        .where(Cart.user_id == user_id)
        .execution_options(populate_existing=True)
    )
    cart = result.scalar_one_or_none()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart, attribute_names=["items"])
    return cart


def _to_read(cart: Cart) -> CartRead:
    from app.schemas.cart import CartItemRead
    from app.schemas.product import ProductRead

    items = []
    total = Decimal("0")
    for item in cart.items:
        product_read = ProductRead.model_validate(item.product)
        items.append(CartItemRead(id=item.id, product=product_read, quantity=item.quantity))
        total += product_read.price * item.quantity

    return CartRead(id=cart.id, items=items, total=total)


async def get_cart(db: AsyncSession, user_id: uuid.UUID) -> CartRead:
    cart = await _get_or_create_cart(db, user_id)
    return _to_read(cart)


async def add_item(db: AsyncSession, user_id: uuid.UUID, item_in: CartItemCreate) -> CartRead:
    cart = await _get_or_create_cart(db, user_id)
    product = await get_product(db, item_in.product_id)

    existing_item = next((i for i in cart.items if i.product_id == item_in.product_id), None)
    new_quantity = (existing_item.quantity if existing_item else 0) + item_in.quantity

    if not product.has_stock(new_quantity):
        raise InsufficientStockError(f"Only {product.stock} unit(s) of '{product.name}' available")

    if existing_item:
        existing_item.quantity = new_quantity
    else:
        db.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=item_in.quantity))

    await db.commit()
    cart = await _get_or_create_cart(db, user_id)
    return _to_read(cart)


async def update_item(
    db: AsyncSession, user_id: uuid.UUID, item_id: uuid.UUID, item_in: CartItemUpdate
) -> CartRead:
    cart = await _get_or_create_cart(db, user_id)
    item = next((i for i in cart.items if i.id == item_id), None)
    if not item:
        raise NotFoundError("Cart item not found")

    product = await get_product(db, item.product_id)
    if not product.has_stock(item_in.quantity):
        raise InsufficientStockError(f"Only {product.stock} unit(s) of '{product.name}' available")

    item.quantity = item_in.quantity
    await db.commit()
    cart = await _get_or_create_cart(db, user_id)
    return _to_read(cart)


async def remove_item(db: AsyncSession, user_id: uuid.UUID, item_id: uuid.UUID) -> CartRead:
    cart = await _get_or_create_cart(db, user_id)
    item = next((i for i in cart.items if i.id == item_id), None)
    if not item:
        raise NotFoundError("Cart item not found")

    await db.delete(item)
    await db.commit()
    cart = await _get_or_create_cart(db, user_id)
    return _to_read(cart)


async def clear_cart(db: AsyncSession, cart: Cart) -> None:
    for item in list(cart.items):
        await db.delete(item)
    await db.commit()
