"""Business logic for checkout and order management."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import EmptyCartError, InsufficientStockError, NotFoundError
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import CheckoutRequest
from app.services.cart_service import clear_cart
from app.services.payment_service import PaymentGateway


async def _get_cart_with_items(db: AsyncSession, user_id: uuid.UUID) -> Cart | None:
    result = await db.execute(
        select(Cart)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
        .where(Cart.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def checkout(
    db: AsyncSession,
    user_id: uuid.UUID,
    checkout_in: CheckoutRequest,
    payment_gateway: PaymentGateway,
) -> Order:
    cart = await _get_cart_with_items(db, user_id)
    if not cart or not cart.items:
        raise EmptyCartError()

    # Validate stock for every line before touching anything (all-or-nothing).
    for item in cart.items:
        if not item.product.has_stock(item.quantity):
            raise InsufficientStockError(
                f"Only {item.product.stock} unit(s) of '{item.product.name}' available"
            )

    total_amount = sum(item.product.price * item.quantity for item in cart.items)

    order = Order(
        user_id=user_id,
        status=OrderStatus.PENDING,
        total_amount=total_amount,
        shipping_address=checkout_in.shipping_address,
    )
    db.add(order)
    await db.flush()

    for item in cart.items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product.id,
                product_name=item.product.name,
                unit_price=item.product.price,
                quantity=item.quantity,
            )
        )
        item.product.stock -= item.quantity  # reserve stock

    payment_reference = await payment_gateway.charge(total_amount)
    order.status = OrderStatus.PAID
    order.payment_reference = payment_reference

    await clear_cart(db, cart)
    await db.commit()

    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
    )
    return result.scalar_one()


async def list_orders(db: AsyncSession, user_id: uuid.UUID) -> list[Order]:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
    )
    return list(result.scalars().all())


async def get_order(db: AsyncSession, order_id: uuid.UUID, user_id: uuid.UUID | None = None) -> Order:
    query = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    if user_id:
        query = query.where(Order.user_id == user_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundError("Order not found")
    return order


async def update_order_status(db: AsyncSession, order_id: uuid.UUID, status: OrderStatus) -> Order:
    order = await get_order(db, order_id)
    order.status = status
    await db.commit()
    await db.refresh(order, attribute_names=["items"])
    return order


async def list_all_orders(db: AsyncSession) -> list[Order]:
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc())
    )
    return list(result.scalars().all())
