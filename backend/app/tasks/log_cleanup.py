from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from ..db.session import get_async_db
from ..models.log_models import SystemLog, AuditLog
from datetime import datetime, timedelta

async def delete_old_logs():
    """
    Deletes old logs from the database.
    """
    async for db in get_async_db():
        # Delete system logs older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        await db.execute(delete(SystemLog).where(SystemLog.timestamp < cutoff_date))
        
        # Delete audit logs older than 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        await db.execute(delete(AuditLog).where(AuditLog.timestamp < cutoff_date))
        
        await db.commit()

scheduler = AsyncIOScheduler()
scheduler.add_job(delete_old_logs, 'interval', days=1)