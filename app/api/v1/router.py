"""Aggregates all v1 endpoint routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, cart, categories, orders, products, reviews, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(users.router, prefix="/users")
api_router.include_router(categories.router, prefix="/categories")
api_router.include_router(products.router, prefix="/products")
api_router.include_router(cart.router, prefix="/cart")
api_router.include_router(orders.router, prefix="/orders")
api_router.include_router(reviews.router, prefix="")
