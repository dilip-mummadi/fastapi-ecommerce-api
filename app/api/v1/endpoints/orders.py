"""Order endpoints: checkout, order history, and admin order management."""
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import CheckoutRequest, OrderRead, OrderStatusUpdate
from app.services import order_service
from app.services.notification_service import send_order_confirmation
from app.services.payment_service import PaymentGateway, get_payment_gateway

router = APIRouter(tags=["orders"])


@router.post("/checkout", response_model=OrderRead, status_code=201)
async def checkout(
    checkout_in: CheckoutRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    payment_gateway: PaymentGateway = Depends(get_payment_gateway),
):
    order = await order_service.checkout(db, current_user.id, checkout_in, payment_gateway)
    background_tasks.add_task(
        send_order_confirmation, current_user.email, str(order.id), str(order.total_amount)
    )
    return order


@router.get("/", response_model=list[OrderRead])
async def list_my_orders(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    return await order_service.list_orders(db, current_user.id)


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return await order_service.get_order(db, order_id, current_user.id)


@router.get(
    "/admin/all", response_model=list[OrderRead], dependencies=[Depends(get_current_admin_user)]
)
async def list_all_orders(db: AsyncSession = Depends(get_db)):
    return await order_service.list_all_orders(db)


@router.patch(
    "/admin/{order_id}/status",
    response_model=OrderRead,
    dependencies=[Depends(get_current_admin_user)],
)
async def update_order_status(
    order_id: uuid.UUID, status_in: OrderStatusUpdate, db: AsyncSession = Depends(get_db)
):
    return await order_service.update_order_status(db, order_id, status_in.status)
