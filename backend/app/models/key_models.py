import uuid
from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from ..db.base import Base

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    key_hash = Column(String, nullable=False)
    label = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    last_used_at = Column(DateTime)

class ExchangeConfig(Base):
    __tablename__ = "exchange_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exchange_name = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    secret_key = Column(String, nullable=False)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())