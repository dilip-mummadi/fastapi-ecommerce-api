"""Import hub: pulls in every ORM model so Base.metadata is fully populated.

Import this package (not the individual model modules) anywhere you need all
tables registered before create_all/Alembic autogenerate — e.g. alembic/env.py
and tests/conftest.py both do `import app.models`.
"""
from app.models.cart import Cart, CartItem  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.order import Order, OrderItem  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.review import Review  # noqa: F401
from app.models.user import User  # noqa: F401
