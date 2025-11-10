from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..models.log_models import SystemLog, AuditLog
from datetime import datetime, timedelta
from typing import List
from ..schemas.log_schemas import SystemLogOut, AuditLogOut
from ..dependencies import require_role
from ..models.user_models import User

router = APIRouter()

@router.get("/system", response_model=List[SystemLogOut])
def get_system_logs(
    level: str = None,
    category: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Get system logs.
    """
    query = db.query(SystemLog)
    if level:
        query = query.filter(SystemLog.level == level)
    if category:
        query = query.filter(SystemLog.category == category)
    if start_date:
        query = query.filter(SystemLog.timestamp >= start_date)
    if end_date:
        query = query.filter(SystemLog.timestamp <= end_date)
    return query.limit(limit).all()

@router.get("/audit", response_model=List[AuditLogOut])
def get_audit_logs(
    user_id: str = None,
    action: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Get audit logs.
    """
    query = db.query(AuditLog)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    return query.limit(limit).all()

@router.delete("/system/{days_old}")
def delete_system_logs(
    days_old: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Delete system logs older than X days.
    """
    if days_old < 0:
        raise HTTPException(status_code=400, detail="days_old must be a positive integer")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    db.query(SystemLog).filter(SystemLog.timestamp < cutoff_date).delete()
    db.commit()
    return {"success": True}

@router.post("/export")
def export_logs(current_user: User = Depends(require_role("admin"))):
    """
    Export logs as CSV/JSON.
    """
    # This is a placeholder. In a real-world application, you would
    # generate a CSV or JSON file and return it as a response.
    return {"success": True}
