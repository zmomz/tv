from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ..db.session import get_async_db
from ..models.log_models import SystemLog, AuditLog
from datetime import datetime, timedelta
from typing import List
from ..schemas.log_schemas import SystemLogOut, AuditLogOut
from ..dependencies import require_role
from ..models.user_models import User

router = APIRouter()

@router.get("")
async def redirect_to_system_logs():
    """
    Redirects to system logs.
    """
    raise HTTPException(status_code=307, detail="Redirecting to /api/logs/system", headers={"Location": "/api/logs/system"})

@router.get("/system", response_model=List[SystemLogOut])
async def get_system_logs(
    level: str = None,
    category: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Get system logs.
    """
    query = select(SystemLog)
    if level:
        query = query.where(SystemLog.level == level)
    if category:
        query = query.where(SystemLog.category == category)
    if start_date:
        query = query.where(SystemLog.timestamp >= start_date)
    if end_date:
        query = query.where(SystemLog.timestamp <= end_date)
    
    result = await db.execute(query.limit(limit))
    return result.scalars().all()

@router.get("/audit", response_model=List[AuditLogOut])
async def get_audit_logs(
    user_id: str = None,
    action: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Get audit logs.
    """
    query = select(AuditLog)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
    if start_date:
        query = query.where(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.where(AuditLog.timestamp <= end_date)
    
    result = await db.execute(query.limit(limit))
    return result.scalars().all()

@router.delete("/system/{days_old}")
async def delete_system_logs(
    days_old: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Delete system logs older than X days.
    """
    if days_old < 0:
        raise HTTPException(status_code=400, detail="days_old must be a positive integer")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    await db.execute(delete(SystemLog).where(SystemLog.timestamp < cutoff_date))
    await db.commit()
    return {"success": True}

@router.post("/export")
async def export_logs(current_user: User = Depends(require_role("admin"))):
    """
    Export logs as CSV/JSON.
    """
    # This is a placeholder. In a real-world application, you would
    # generate a CSV or JSON file and return it as a response.
    return {"success": True}