from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.session import get_async_db
from ..services.health_service import check_system_health, check_database_health

router = APIRouter()

@router.get("/health", response_model=dict)
async def get_health_status(
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retrieve the current health status of the application and its components.
    """
    system_health = await check_system_health()
    database_health = await check_database_health()
    # You can add more detailed health checks here, e.g., Redis, Exchange connections
    return {
        "status": system_health["status"],
        "database": database_health["status"],
        "redis": "connected", # Placeholder for actual Redis health check
    }
