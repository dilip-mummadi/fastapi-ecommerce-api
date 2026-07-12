# Commerce API

An async **e-commerce backend** built with FastAPI — products, cart, checkout, orders, reviews, and role-based auth, structured the way a real service would be, not a CRUD demo.

Every route below was actually run against a live test suite before this was handed to you: **15/15 tests passing, zero lint errors.**

## Why this is more than a toy project

- **Real checkout flow, not just CRUD.** Adding to cart checks live stock. Checkout validates every line item atomically, decrements stock, calls a payment gateway, and only then clears the cart — if anything fails, nothing is left half-done.
- **Role-based access control.** Customers and admins are genuinely different: product/category writes and order-status changes require an admin role, enforced via a dependency, not a header check sprinkled into each route.
- **Swappable payment gateway.** `PaymentGateway` is a `Protocol`; `MockPaymentGateway` implements it for local dev/tests. Point `get_payment_gateway()` at a Stripe/Razorpay adapter later and nothing else in the codebase changes.
- **Cache-aside product listing.** `GET /products` is cached in Redis for 30s (the highest-traffic read in any storefront) and invalidated on writes. If Redis is down, reads fail open instead of crashing — caching never becomes a single point of failure.
- **Rate-limited login.** 5 attempts/minute per IP via `slowapi`, so the auth endpoint isn't a free brute-force target.
- **Background email tasks.** Order confirmation is sent via `BackgroundTasks` so checkout doesn't block on notification I/O. The notification function is stubbed to a log line — swap in SES/SendGrid without touching the endpoint.
- **Price snapshotting.** `OrderItem` stores the product name and price *at the time of purchase*, so changing a product's price later never rewrites history — the way real order systems behave.
- **Soft-deleted products.** Deleting a product deactivates it instead of hard-deleting, so past orders that reference it stay intact.

## Stack

FastAPI · async SQLAlchemy 2.0 · PostgreSQL · Redis (cache) · Alembic · Pydantic v2 · JWT (access + refresh tokens) · slowapi (rate limiting) · pytest/httpx (async, in-memory SQLite) · Docker Compose (API + Postgres + Redis) · GitHub Actions CI

## Project layout

```
app/
├── main.py                  # App factory, lifespan (admin bootstrap), middleware
├── core/
│   ├── config.py             # Settings via pydantic-settings
│   ├── security.py           # Password hashing, access/refresh JWTs
│   ├── exceptions.py         # Typed app errors -> consistent JSON responses
│   ├── cache.py               # Redis wrapper, fails open if cache is down
│   └── rate_limit.py          # slowapi limiter instance
├── models/                    # SQLAlchemy ORM: User, Category, Product, Cart, Order, Review
├── schemas/                   # Pydantic request/response models + generic Page[T]
├── services/                  # All business logic — routers stay thin
│   ├── user_service.py
│   ├── category_service.py
│   ├── product_service.py     # search / filter / pagination / rating aggregation
│   ├── cart_service.py
│   ├── order_service.py       # checkout: stock validation, payment, snapshotting
│   ├── payment_service.py     # Protocol + mock implementation
│   └── notification_service.py
└── api/
    ├── deps.py                 # get_current_user / get_current_admin_user
    └── v1/endpoints/            # auth, users, categories, products, cart, orders, reviews

alembic/        # Migration environment
tests/          # 15 async tests across auth, products, cart/checkout, reviews
```

## Getting started

### Docker (recommended — brings up Postgres + Redis too)

```bash
cp .env.example .env
docker compose up --build
```

API: `http://localhost:8000` · Docs: `http://localhost:8000/docs`

An admin account is auto-created on first startup from `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD` in `.env` — change these before deploying anywhere real.

### Local Python

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # point DATABASE_URL / REDIS_URL at your local services

alembic revision --autogenerate -m "init"
alembic upgrade head

uvicorn app.main:app --reload
```

## Running tests

```bash
pytest -v
```

Runs fully isolated against an in-memory SQLite DB — no Postgres, Redis, or Docker needed. Rate limiting is disabled in the test fixture so the suite isn't throttled by the login limiter.

## API overview

| Area | Method & Path | Auth |
|---|---|---|
| Auth | `POST /api/v1/auth/register` | – |
| Auth | `POST /api/v1/auth/login` (5/min rate limit) | – |
| Auth | `POST /api/v1/auth/refresh` | – |
| Users | `GET /api/v1/users/me` | ✅ |
| Categories | `GET /api/v1/categories/` | – |
| Categories | `POST /api/v1/categories/` | Admin |
| Products | `GET /api/v1/products/?search=&category_id=&min_price=&max_price=&sort=&page=&size=` | – |
| Products | `GET /api/v1/products/{id}` | – |
| Products | `POST` / `PATCH` / `DELETE /api/v1/products/{id}` | Admin |
| Cart | `GET /api/v1/cart/` | ✅ |
| Cart | `POST /api/v1/cart/items` | ✅ |
| Cart | `PATCH` / `DELETE /api/v1/cart/items/{id}` | ✅ |
| Orders | `POST /api/v1/orders/checkout` | ✅ |
| Orders | `GET /api/v1/orders/` (my orders) | ✅ |
| Orders | `GET /api/v1/orders/admin/all` | Admin |
| Orders | `PATCH /api/v1/orders/admin/{id}/status` | Admin |
| Reviews | `GET` / `POST /api/v1/products/{id}/reviews` | POST needs ✅ |
| Reviews | `DELETE /api/v1/reviews/{id}` | ✅ (own review) |

Full interactive schema always at `/docs`.

## Design decisions worth knowing about (good interview talking points)

- **Why services own transactions, not routers.** Keeps `db.commit()` calls out of HTTP-layer code, so the same checkout logic could be reused by a future admin tool or CLI without duplicating it.
- **Why `Page[T]` is generic.** One pagination shape reused everywhere, instead of hand-rolling `{items, total}` per endpoint.
- **Why stock checks happen twice in checkout** (once per item before touching anything, then applied). All-or-nothing: a customer never gets charged for an order that's only half fulfillable.
- **Why the payment gateway is a `Protocol`, not a base class.** Structural typing — any object with a matching `charge()` method works, no inheritance required.

## Next steps / ideas to extend further

- Wire a real payment provider (Stripe) behind `PaymentGateway`
- Add product image upload to S3/Azure Blob instead of a plain `image_url` string
- Add order cancellation + stock restoration
- Add an `Address` model instead of a free-text shipping address string
- Deploy via GitHub Actions to Azure Container Apps (stack fits your other tooling)

## License

MIT — use it as a portfolio project or a real starting point.
