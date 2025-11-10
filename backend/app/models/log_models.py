import uuid
from sqlalchemy import Column, DateTime, Enum, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..db.base import Base

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=func.now())
    level = Column(Enum('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', name='log_level'), nullable=False)
    category = Column(Enum('SECURITY', 'TRADING', 'SYSTEM', 'RISK', 'API', name='log_category'), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=func.now())
    user_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=False)