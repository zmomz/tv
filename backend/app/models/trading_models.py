import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Integer, Text, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSON
from ..db.base import Base
import sqlalchemy as sa

class PositionGroup(Base):
    __tablename__ = "position_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exchange_config_id = Column(UUID(as_uuid=True), ForeignKey("exchange_configs.id"), nullable=False)
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    status = Column(Enum('waiting', 'live', 'partially_filled', 'closing', 'closed', 'failed', name='position_group_status'), nullable=False)
    unrealized_pnl_percent = Column(DECIMAL(10, 4), nullable=True)
    unrealized_pnl_usd = Column(DECIMAL(20, 8), nullable=True)
    entry_signal = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class DCAOrder(Base):
    __tablename__ = "dca_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    position_group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), nullable=False)
    pyramid_level = Column(Integer, nullable=False)
    dca_level = Column(Integer, nullable=False)
    price_gap_percent = Column(DECIMAL(5, 2), nullable=False)
    capital_weight_percent = Column(DECIMAL(5, 2), nullable=False)
    take_profit_percent = Column(DECIMAL(5, 2), nullable=False)
    expected_price = Column(DECIMAL(20, 8), nullable=False)
    quantity = Column(DECIMAL(20, 8), nullable=False)
    filled_price = Column(DECIMAL(20, 8), nullable=True)
    filled_quantity = Column(DECIMAL(20, 8), nullable=True)
    status = Column(Enum('pending', 'filled', 'cancelled', 'failed', name='dca_order_status'), nullable=False)
    exchange_order_id = Column(String(100), nullable=True)

class Pyramid(Base):
    __tablename__ = "pyramids"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    position_group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), nullable=False)
    pyramid_level = Column(Integer, nullable=False)
    status = Column(Enum('pending', 'active', 'closed', 'failed', name='pyramid_status'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class QueueEntry(Base):
    __tablename__ = "queue_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    original_signal = Column(JSON, nullable=False)
    priority_score = Column(DECIMAL(10, 4), nullable=True)
    replacement_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
