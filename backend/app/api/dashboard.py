from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.session import get_async_db
from ..schemas.dashboard_schemas import DashboardStats
from ..services.dashboard_service import get_dashboard_stats

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get dashboard statistics.
    """
    return await get_dashboard_stats(db)
