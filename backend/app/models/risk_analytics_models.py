import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Integer, Text, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSON
from ..db.base import Base
import sqlalchemy as sa

class RiskAnalysis(Base):
    __tablename__ = "risk_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    position_group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), nullable=False)
    losing_position_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), nullable=True)
    winning_positions_ids = Column(JSON, nullable=True) # List of UUIDs
    required_usd_offset = Column(DECIMAL(20, 8), nullable=False)
    actual_usd_offset = Column(DECIMAL(20, 8), nullable=False)
    action_taken = Column(String(100), nullable=False) # e.g., "partial_close_winners", "full_close_loser"
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class TradeAnalytics(Base):
    __tablename__ = "trade_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    position_group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), unique=True, nullable=False)
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    entry_price_avg = Column(DECIMAL(20, 8), nullable=True)
    exit_price_avg = Column(DECIMAL(20, 8), nullable=True)
    realized_pnl_usd = Column(DECIMAL(20, 8), nullable=False)
    realized_pnl_percent = Column(DECIMAL(10, 4), nullable=False)
    roi_percent = Column(DECIMAL(10, 4), nullable=False)
    max_drawdown_percent = Column(DECIMAL(10, 4), nullable=True)
    holding_period_minutes = Column(Integer, nullable=True)
    entry_count = Column(Integer, nullable=False)
    dca_fill_count = Column(Integer, nullable=False)
    exit_type = Column(Enum('TP', 'Risk', 'Manual', 'Webhook_Exit', name='trade_exit_type'), nullable=False)
    closed_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
