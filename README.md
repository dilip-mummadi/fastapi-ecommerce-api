<div align="center">

# 🛒 FastAPI E-Commerce API

**A production-grade, async e-commerce backend — not a CRUD demo.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat&logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Tests](https://img.shields.io/badge/Tests-15%20passing-brightgreen?style=flat&logo=pytest)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](LICENSE)

[Features](#-features) · [Tech Stack](#-tech-stack) · [Quick Start](#-quick-start) · [API Reference](#-api-reference) · [Architecture](#-architecture) · [Testing](#-testing) · [Roadmap](#-roadmap)

</div>

---

## Overview

A fully async, production-ready RESTful API for an e-commerce platform, built with **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL**, and **Redis**. It covers the full customer journey — registration, browsing, cart, checkout, order management, and product reviews — with proper role-based access control throughout.

Every endpoint has been validated against a live test suite: **15/15 tests passing, zero lint errors.**

---

## ✨ Features

| Feature | Details |
|---|---|
| **Atomic Checkout** | Stock validated per item before any mutation. Payment, stock decrement, and cart clear happen as a unit — partial failures roll back entirely |
| **Role-Based Access Control** | `customer` vs `admin` enforced via FastAPI dependencies — not scattered header checks |
| **JWT Auth (Access + Refresh)** | Short-lived access tokens, long-lived refresh tokens, secure password hashing via bcrypt |
| **Redis Cache-Aside** | Product listings cached for 30s; invalidated on writes. Fails open — Redis outage never crashes the API |
| **Rate-Limited Login** | 5 attempts / minute / IP via `slowapi` to block brute-force attacks |
| **Price Snapshotting** | `OrderItem` captures product name and price at purchase time — changing a product price never rewrites order history |
| **Soft Delete** | Products are deactivated, not hard-deleted, preserving referential integrity with existing orders |
| **Background Notifications** | Order confirmations dispatched via `BackgroundTasks` — checkout response time is never blocked by email I/O |
| **Swappable Payment Gateway** | `PaymentGateway` is a `Protocol` — swap `MockPaymentGateway` for a real Stripe adapter without touching any endpoint code |
| **Generic Pagination** | `Page[T]` schema reused across every list endpoint — consistent `{items, total, page, size}` shape everywhere |
| **Auto Admin Bootstrap** | First admin account created on startup from env vars — no manual SQL seeds needed |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | FastAPI 0.115 + Uvicorn |
| **Database** | PostgreSQL 16 via async SQLAlchemy 2.0 + asyncpg |
| **Migrations** | Alembic |
| **Validation** | Pydantic v2 + pydantic-settings |
| **Auth** | JWT (python-jose) + bcrypt (passlib) |
| **Cache** | Redis 7 |
| **Rate Limiting** | slowapi |
| **Testing** | pytest-asyncio + httpx (async, in-memory SQLite — no Docker needed) |
| **Containerization** | Docker + Docker Compose (API + PostgreSQL + Redis) |

---

## 🚀 Quick Start

### Option 1 — Docker (recommended)

Spins up the API, PostgreSQL, and Redis in one command:

```bash
git clone https://github.com/DilipKumarMummadi/fastapi-ecommerce-api.git
cd fastapi-ecommerce-api

cp .env.example .env          # review and adjust secrets
docker compose up --build
```

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/health |

> **First-run admin account** is created automatically from `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD` in your `.env`. Change these before any real deployment.

---

### Option 2 — Local Python

```bash
# 1. Clone & create virtualenv
git clone https://github.com/DilipKumarMummadi/fastapi-ecommerce-api.git
cd fastapi-ecommerce-api
python -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements-dev.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — point DATABASE_URL and REDIS_URL at your local services

# 4. Run database migrations
alembic upgrade head

# 5. Start the server
uvicorn app.main:app --reload
```

---

## 📁 Project Structure

```
fastapi-ecommerce-api/
├── app/
│   ├── main.py                        # App factory, lifespan, CORS, middleware
│   ├── core/
│   │   ├── config.py                  # Settings (pydantic-settings, env-driven)
│   │   ├── security.py                # Password hashing, JWT creation/verification
│   │   ├── exceptions.py              # Typed domain errors → consistent JSON responses
│   │   ├── cache.py                   # Redis wrapper (fail-open design)
│   │   └── rate_limit.py              # slowapi limiter instance
│   ├── db/
│   │   ├── session.py                 # Async engine + session factory
│   │   └── base.py                    # Declarative base + model imports
│   ├── models/                        # SQLAlchemy ORM models
│   │   ├── user.py                    # User (role: customer | admin)
│   │   ├── category.py
│   │   ├── product.py                 # Soft-delete, stock tracking
│   │   ├── cart.py                    # CartItem (linked to live Product)
│   │   ├── order.py                   # Order + OrderItem (price snapshot)
│   │   └── review.py
│   ├── schemas/                       # Pydantic v2 request / response models
│   │   ├── common.py                  # Generic Page[T] pagination schema
│   │   └── ...
│   ├── services/                      # Business logic layer (owns transactions)
│   │   ├── user_service.py
│   │   ├── category_service.py
│   │   ├── product_service.py         # Search, filter, sort, pagination, rating avg
│   │   ├── cart_service.py
│   │   ├── order_service.py           # Atomic checkout: validate → charge → commit
│   │   ├── payment_service.py         # PaymentGateway Protocol + MockPaymentGateway
│   │   ├── notification_service.py    # Background email stub (swap in SES/SendGrid)
│   │   └── review_service.py
│   └── api/
│       ├── deps.py                    # get_current_user / require_admin dependencies
│       └── v1/
│           ├── router.py
│           └── endpoints/             # Thin routers — all logic lives in services
│               ├── auth.py
│               ├── users.py
│               ├── categories.py
│               ├── products.py
│               ├── cart.py
│               ├── orders.py
│               └── reviews.py
├── alembic/                           # Database migration environment
├── tests/                             # 15 async integration tests
│   ├── conftest.py                    # In-memory SQLite fixtures, test client
│   ├── test_auth.py
│   ├── test_products.py
│   ├── test_cart_and_orders.py
│   └── test_reviews.py
├── docker-compose.yml                 # API + PostgreSQL 16 + Redis 7
├── Dockerfile
├── alembic.ini
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

---

## 📡 API Reference

> Full interactive schema always available at `/docs` (Swagger UI) or `/redoc`.

### Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | — | Register new customer account |
| `POST` | `/api/v1/auth/login` | — | Login (rate-limited: 5/min/IP) → returns JWT pair |
| `POST` | `/api/v1/auth/refresh` | — | Exchange refresh token for new access token |

### Users

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/users/me` | ✅ User | Get current user profile |

### Categories

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/categories/` | — | List all categories |
| `POST` | `/api/v1/categories/` | 🔐 Admin | Create category |
| `PATCH` | `/api/v1/categories/{id}` | 🔐 Admin | Update category |
| `DELETE` | `/api/v1/categories/{id}` | 🔐 Admin | Delete category |

### Products

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/products/` | — | List with search, filter, sort, pagination |
| `GET` | `/api/v1/products/{id}` | — | Get product detail |
| `POST` | `/api/v1/products/` | 🔐 Admin | Create product |
| `PATCH` | `/api/v1/products/{id}` | 🔐 Admin | Update product |
| `DELETE` | `/api/v1/products/{id}` | 🔐 Admin | Soft-delete product |

**Query params for `GET /products/`:** `search` · `category_id` · `min_price` · `max_price` · `sort` (`price_asc`, `price_desc`, `rating`) · `page` · `size`

### Cart

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/cart/` | ✅ User | View cart |
| `POST` | `/api/v1/cart/items` | ✅ User | Add item (checks live stock) |
| `PATCH` | `/api/v1/cart/items/{id}` | ✅ User | Update item quantity |
| `DELETE` | `/api/v1/cart/items/{id}` | ✅ User | Remove item |

### Orders

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/orders/checkout` | ✅ User | Atomic checkout — validate stock → charge → clear cart |
| `GET` | `/api/v1/orders/` | ✅ User | List my orders |
| `GET` | `/api/v1/orders/admin/all` | 🔐 Admin | List all orders |
| `PATCH` | `/api/v1/orders/admin/{id}/status` | 🔐 Admin | Update order status |

### Reviews

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/products/{id}/reviews` | — | List reviews for product |
| `POST` | `/api/v1/products/{id}/reviews` | ✅ User | Submit review |
| `DELETE` | `/api/v1/reviews/{id}` | ✅ User | Delete own review |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI App                      │
│                                                     │
│   ┌──────────┐   ┌──────────┐   ┌──────────────┐   │
│   │  Router  │──▶│ Service  │──▶│  Repository  │   │
│   │ (thin)   │   │(business │   │(SQLAlchemy)  │   │
│   └──────────┘   │  logic)  │   └──────┬───────┘   │
│                  └────┬─────┘          │            │
│                       │                ▼            │
│              ┌────────┴──────┐   ┌──────────┐      │
│              │ Redis Cache   │   │PostgreSQL│      │
│              │ (fail-open)   │   │    16    │      │
│              └───────────────┘   └──────────┘      │
└─────────────────────────────────────────────────────┘
```

**Key design choices:**

- **Services own transactions** — `db.commit()` never lives in a router. The same service can be called from HTTP handlers, CLI scripts, or background jobs.
- **Fail-open cache** — A Redis outage silently bypasses the cache layer; it never propagates as a 500 to the client.
- **Protocol-based payment gateway** — Structural typing means any object with a matching `charge()` method qualifies. No inheritance, no mocking frameworks needed in tests.
- **Double stock check in checkout** — All items are validated before any mutation. A customer is never charged for an order that's only partially fulfillable.

---

## 🧪 Testing

```bash
# Run the full test suite
pytest -v

# With coverage
pytest -v --cov=app --cov-report=term-missing
```

Tests run against an **in-memory SQLite database** — no PostgreSQL, Redis, or Docker required. Rate limiting is disabled in the test fixture so the suite isn't throttled.

```
tests/test_auth.py             — registration, login, token refresh, rate limiting
tests/test_products.py         — CRUD, search, filtering, admin-only guards
tests/test_cart_and_orders.py  — add to cart, checkout flow, stock validation
tests/test_reviews.py          — submit, list, delete own review
```

---

## 🗺 Roadmap

- [ ] Stripe / Razorpay adapter behind `PaymentGateway` protocol
- [ ] Product image upload to S3 / Azure Blob Storage
- [ ] Order cancellation with stock restoration
- [ ] `Address` model (replacing free-text shipping address)
- [ ] Admin dashboard metrics endpoint (revenue, top products)
- [ ] GitHub Actions CI/CD → deploy to Azure Container Apps

---

## 📄 License

MIT — use it as a portfolio project, a learning resource, or a real starting point.

---

<div align="center">
Built with FastAPI · PostgreSQL · Redis · Docker
</div>
