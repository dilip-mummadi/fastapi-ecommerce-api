"""Category endpoints. Reads are public; writes require admin."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.schemas.category import CategoryCreate, CategoryRead
from app.services import category_service

router = APIRouter(tags=["categories"])


@router.get("/", response_model=list[CategoryRead])
async def list_categories(db: AsyncSession = Depends(get_db)):
    return await category_service.list_categories(db)


@router.post(
    "/", response_model=CategoryRead, status_code=201, dependencies=[Depends(get_current_admin_user)]
)
async def create_category(category_in: CategoryCreate, db: AsyncSession = Depends(get_db)):
    return await category_service.create_category(db, category_in)
