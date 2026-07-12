"""FastAPI application entrypoint."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.rate_limit import limiter
from app.db.session import AsyncSessionLocal
from app.schemas.user import UserCreate
from app.services.user_service import create_user, get_user_by_email

logger = logging.getLogger("commerce")


async def _bootstrap_admin() -> None:
    """Create a first admin account on startup if one doesn't already exist."""
    async with AsyncSessionLocal() as db:
        existing = await get_user_by_email(db, settings.FIRST_ADMIN_EMAIL)
        if existing:
            return
        from app.models.user import UserRole

        user = await create_user(
            db,
            UserCreate(
                email=settings.FIRST_ADMIN_EMAIL,
                full_name="Admin",
                password=settings.FIRST_ADMIN_PASSWORD,
            ),
        )
        user.role = UserRole.ADMIN
        await db.commit()
        logger.info("Bootstrapped admin account: %s", settings.FIRST_ADMIN_EMAIL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.DEBUG)
    await _bootstrap_admin()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
register_exception_handlers(app)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
