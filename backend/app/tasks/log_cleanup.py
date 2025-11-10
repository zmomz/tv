from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.log_models import SystemLog, AuditLog
from datetime import datetime, timedelta

def delete_old_logs():
    """
    Deletes old logs from the database.
    """
    db: Session = next(get_db())
    
    # Delete system logs older than 30 days
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    db.query(SystemLog).filter(SystemLog.timestamp < cutoff_date).delete()
    
    # Delete audit logs older than 90 days
    cutoff_date = datetime.utcnow() - timedelta(days=90)
    db.query(AuditLog).filter(AuditLog.timestamp < cutoff_date).delete()
    
    db.commit()
    db.close()

scheduler = AsyncIOScheduler()
scheduler.add_job(delete_old_logs, 'interval', days=1)
