import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from ..db.base import Base
import sqlalchemy as sa

class ExchangeConfig(Base):
    __tablename__ = "exchange_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exchange_name = Column(String(50), nullable=False)
    mode = Column(Enum('testnet', 'live', name='exchange_mode'), nullable=False)
    api_key_encrypted = Column(Text, nullable=False)
    api_secret_encrypted = Column(Text, nullable=False)
    is_enabled = Column(Boolean, default=False, nullable=False)
    is_validated = Column(Boolean, default=False, nullable=False)
    last_validated = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
