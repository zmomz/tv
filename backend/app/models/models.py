import uuid
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from ..db.base import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exchange = Column(String, nullable=False)
    encrypted_api_key = Column(String, nullable=False)
    encrypted_secret = Column(String, nullable=False)
    is_testnet = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

class QueuedSignal(Base):
    __tablename__ = "queued_signals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    pair = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    payload = Column(String, nullable=False) # Store the raw webhook payload as a string
    status = Column(String, default="queued", nullable=False) # e.g., "queued", "processing", "processed", "cancelled"
    replacement_count = Column(Integer, default=0)
    priority_rank = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    payload = Column(String, nullable=False)
    status = Column(String, nullable=False) # e.g., "received", "processed", "error"
    error_message = Column(String, nullable=True)
