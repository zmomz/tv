from sqlalchemy.orm import Session
from ..models.log_models import SystemLog, AuditLog
from uuid import UUID

def log_debug(db: Session, category: str, message: str, user_id: UUID = None, details: dict = None):
    log(db, "DEBUG", category, message, user_id, details)

def log_info(db: Session, category: str, message: str, user_id: UUID = None, details: dict = None):
    log(db, "INFO", category, message, user_id, details)

def log_warning(db: Session, category: str, message: str, user_id: UUID = None, details: dict = None):
    log(db, "WARNING", category, message, user_id, details)

def log_error(db: Session, category: str, message: str, user_id: UUID = None, details: dict = None):
    log(db, "ERROR", category, message, user_id, details)

def log_critical(db: Session, category: str, message: str, user_id: UUID = None, details: dict = None):
    log(db, "CRITICAL", category, message, user_id, details)

def log(db: Session, level: str, category: str, message: str, user_id: UUID = None, details: dict = None):
    log_entry = SystemLog(
        level=level,
        category=category,
        message=message,
        user_id=user_id,
        details=details,
    )
    db.add(log_entry)
    db.commit()

def audit_log(db: Session, user_id: UUID, action: str, resource: str, resource_id: str = None, details: dict = None):
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        details=details,
    )
    db.add(log_entry)
    db.commit()
