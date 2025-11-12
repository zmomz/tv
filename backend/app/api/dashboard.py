from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..schemas.dashboard_schemas import DashboardStats
from ..services.dashboard_service import get_dashboard_stats

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: Session = Depends(get_db),
):
    """
    Get dashboard statistics.
    """
    return get_dashboard_stats(db)
