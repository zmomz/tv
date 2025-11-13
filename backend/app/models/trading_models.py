from sqlalchemy import (Column, String, Integer, Numeric, DateTime, Boolean, JSON, ForeignKey, Enum as SQLAlchemyEnum)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from ..db.base import Base

class PositionGroupStatus(str, Enum):
    WAITING = "waiting"
    LIVE = "live"
    PARTIALLY_FILLED = "partially_filled"
    ACTIVE = "active"
    CLOSING = "closing"
    CLOSED = "closed"
    FAILED = "failed"

class PositionGroup(Base):
    """
    Represents a unique trading position defined by pair + timeframe.
    Contains multiple pyramids and DCA legs.
    """
    __tablename__ = "position_groups"
    
    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exchange_config_id = Column(UUID(as_uuid=True), ForeignKey("exchange_configs.id"), nullable=False)
    exchange = Column(String, nullable=False)  # "binance", "bybit", etc.
    symbol = Column(String, nullable=False)  # "BTCUSDT"
    timeframe = Column(Integer, nullable=False)  # in minutes (e.g., 15, 60, 240)
    side = Column(SQLAlchemyEnum("long", "short", name="position_side_enum"), nullable=False)
    
    # Status tracking
    status = Column(SQLAlchemyEnum(PositionGroupStatus, name="group_status_enum"), nullable=False, default=PositionGroupStatus.WAITING)
    
    # Pyramid tracking
    pyramid_count = Column(Integer, default=0)
    max_pyramids = Column(Integer, default=5)
    replacement_count = Column(Integer, default=0)
    
    # DCA tracking
    total_dca_legs = Column(Integer, nullable=False)
    filled_dca_legs = Column(Integer, default=0)
    
    # Financial metrics
    base_entry_price = Column(Numeric(20, 10), nullable=False)
    weighted_avg_entry = Column(Numeric(20, 10), nullable=False)
    total_invested_usd = Column(Numeric(20, 10), default=Decimal("0"))
    total_filled_quantity = Column(Numeric(20, 10), default=Decimal("0"))
    unrealized_pnl_usd = Column(Numeric(20, 10), default=Decimal("0"))
    unrealized_pnl_percent = Column(Numeric(10, 4), default=Decimal("0"))
    realized_pnl_usd = Column(Numeric(20, 10), default=Decimal("0"))
    
    # Take-profit configuration
    tp_mode = Column(SQLAlchemyEnum("per_leg", "aggregate", "hybrid", name="tp_mode_enum"), nullable=False)
    tp_aggregate_percent = Column(Numeric(10, 4))
    
    # Risk engine tracking
    risk_timer_start = Column(DateTime)
    risk_timer_expires = Column(DateTime)
    risk_eligible = Column(Boolean, default=False)
    risk_blocked = Column(Boolean, default=False)
    risk_skip_once = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime)
    
    # Relationships
    pyramids = relationship("Pyramid", back_populates="group", cascade="all, delete-orphan")
    dca_orders = relationship("DCAOrder", back_populates="group", cascade="all, delete-orphan")
    risk_actions = relationship("RiskAction", back_populates="group", cascade="all, delete-orphan", foreign_keys="RiskAction.group_id")

class Pyramid(Base):
    """
    Represents a single pyramid entry within a PositionGroup.
    """
    __tablename__ = "pyramids"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), nullable=False)
    pyramid_index = Column(Integer, nullable=False) # 0-4
    
    entry_price = Column(Numeric(20, 10), nullable=False)
    entry_timestamp = Column(DateTime, nullable=False)
    signal_id = Column(String) # TradingView signal ID
    
    status = Column(SQLAlchemyEnum("pending", "submitted", "filled", "cancelled", "failed", name="pyramid_status_enum"), nullable=False, default="pending")
    dca_config = Column(JSON, nullable=False)
    
    group = relationship("PositionGroup", back_populates="pyramids")
    dca_orders = relationship("DCAOrder", back_populates="pyramid", cascade="all, delete-orphan")

class DCAOrder(Base):
    """
    Represents a single DCA order (limit order at specific price level).
    """
    __tablename__ = "dca_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), nullable=False)
    pyramid_id = Column(UUID(as_uuid=True), ForeignKey("pyramids.id"), nullable=False)
    
    exchange_order_id = Column(String)
    leg_index = Column(Integer, nullable=False)
    
    symbol = Column(String, nullable=False)
    side = Column(SQLAlchemyEnum("buy", "sell", name="order_side_enum"), nullable=False)
    order_type = Column(SQLAlchemyEnum("limit", "market", name="order_type_enum"), default="limit")
    price = Column(Numeric(20, 10), nullable=False)
    quantity = Column(Numeric(20, 10), nullable=False)
    
    gap_percent = Column(Numeric(10, 4), nullable=False)
    weight_percent = Column(Numeric(10, 4), nullable=False)
    tp_percent = Column(Numeric(10, 4), nullable=False)
    tp_price = Column(Numeric(20, 10), nullable=False)
    
    status = Column(SQLAlchemyEnum("pending", "open", "partially_filled", "filled", "cancelled", "failed", name="order_status_enum"), nullable=False, default="pending")
    filled_quantity = Column(Numeric(20, 10), default=Decimal("0"))
    avg_fill_price = Column(Numeric(20, 10))
    
    tp_hit = Column(Boolean, default=False)
    tp_order_id = Column(String)
    tp_executed_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime)
    filled_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    
    group = relationship("PositionGroup", back_populates="dca_orders")
    pyramid = relationship("Pyramid", back_populates="dca_orders")

class QueuedSignal(Base):
    """
    Represents a signal waiting in the queue.
    """
    __tablename__ = "queued_signals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    exchange = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    timeframe = Column(Integer, nullable=False)
    side = Column(SQLAlchemyEnum("long", "short", name="signal_side_enum"), nullable=False)
    entry_price = Column(Numeric(20, 10), nullable=False)
    signal_payload = Column(JSON, nullable=False)
    
    queued_at = Column(DateTime, default=datetime.utcnow)
    replacement_count = Column(Integer, default=0)
    priority_score = Column(Numeric(20, 4), default=0.0)
    
    is_pyramid_continuation = Column(Boolean, default=False)
    current_loss_percent = Column(Numeric(10, 4))
    
    status = Column(SQLAlchemyEnum("queued", "promoted", "cancelled", name="queue_status_enum"), nullable=False, default="queued")
    promoted_at = Column(DateTime)