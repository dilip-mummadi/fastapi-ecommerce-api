"""Custom application exceptions + centralized JSON error handlers."""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base class for predictable, well-typed application errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    detail = "An error occurred"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.detail


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Resource conflict"


class InsufficientStockError(AppError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Not enough stock available"


class EmptyCartError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Cart is empty"


class PaymentError(AppError):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    detail = "Payment failed"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
