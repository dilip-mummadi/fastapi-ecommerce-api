"""Cart schemas."""
import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductRead


class CartItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(default=1, gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CartItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product: ProductRead
    quantity: int

    @property
    def subtotal(self) -> Decimal:
        return self.product.price * self.quantity


class CartRead(BaseModel):
    id: uuid.UUID
    items: list[CartItemRead]
    total: Decimal


