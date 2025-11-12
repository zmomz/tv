import uuid
from sqlalchemy import Column, String, DateTime, func, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..db.base import Base

class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String, nullable=False)
    payload = Column(JSONB)
    error_message = Column(Text)
    received_at = Column(DateTime, default=func.now())

class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    service = Column(String) # e.g., "OrderService", "RiskEngine"
    error_message = Column(Text)
    traceback = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=func.now())

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String, default="INFO")
    timestamp = Column(DateTime, default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String, nullable=False)
    details = Column(Text)
    timestamp = Column(DateTime, default=func.now())