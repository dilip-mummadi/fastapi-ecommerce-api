"""Order schemas."""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus


class CheckoutRequest(BaseModel):
    shipping_address: str = Field(min_length=5)


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    unit_price: Decimal
    quantity: int


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: OrderStatus
    total_amount: Decimal
    shipping_address: str
    payment_reference: str | None
    items: list[OrderItemRead]
    created_at: datetime


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
