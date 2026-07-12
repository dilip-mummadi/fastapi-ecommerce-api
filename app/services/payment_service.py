"""Payment processing, abstracted behind a simple interface.

This mock implementation always succeeds (unless the amount is invalid) and
returns a fake reference id, so the checkout flow is fully testable without
hitting a real payment provider. Swap `MockPaymentGateway` for a Stripe/
Razorpay/Braintree adapter that implements the same `charge()` signature and
nothing else in the codebase needs to change.
"""
import uuid
from decimal import Decimal
from typing import Protocol

from app.core.exceptions import PaymentError


class PaymentGateway(Protocol):
    async def charge(self, amount: Decimal, *, currency: str = "usd") -> str: ...


class MockPaymentGateway:
    async def charge(self, amount: Decimal, *, currency: str = "usd") -> str:
        if amount <= 0:
            raise PaymentError("Charge amount must be greater than zero")
        return f"mock_pay_{uuid.uuid4().hex[:16]}"


def get_payment_gateway() -> PaymentGateway:
    return MockPaymentGateway()
