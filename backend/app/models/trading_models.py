from sqlalchemy import (
    Column, String, Integer, Numeric, DateTime, Boolean, JSON, ForeignKey, Enum as SQLAlchemyEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from decimal import Decimal

from app.db.base import Base

class PositionGroup(Base):
    """
    Represents a unique trading position defined by pair + timeframe.
    Contains multiple pyramids and DCA legs.
    """
    __tablename__ = "position_groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exchange = Column(String, nullable=False)
    symbol = Column(String, nullable=False, index=True)
    timeframe = Column(Integer, nullable=False, index=True)
    side = Column(SQLAlchemyEnum("long", "short", name="position_side_enum"), nullable=False)
    
    status = Column(SQLAlchemyEnum(
        "waiting", "live", "partially_filled", "active", "closing", "closed", "failed",
        name="group_status_enum"
    ), nullable=False, default="waiting", index=True)
    
    pyramid_count = Column(Integer, default=0)
    max_pyramids = Column(Integer, default=5)
    replacement_count = Column(Integer, default=0)
    
    total_dca_legs = Column(Integer, nullable=False)
    filled_dca_legs = Column(Integer, default=0)
    
    base_entry_price = Column(Numeric(20, 10), nullable=False)
    weighted_avg_entry = Column(Numeric(20, 10), nullable=False)
    total_invested_usd = Column(Numeric(20, 10), default=Decimal("0"))
    total_filled_quantity = Column(Numeric(20, 10), default=Decimal("0"))
    unrealized_pnl_usd = Column(Numeric(20, 10), default=Decimal("0"))
    unrealized_pnl_percent = Column(Numeric(10, 4), default=Decimal("0"))
    realized_pnl_usd = Column(Numeric(20, 10), default=Decimal("0"))
    
    tp_mode = Column(SQLAlchemyEnum("per_leg", "aggregate", "hybrid", name="tp_mode_enum"), nullable=False)
    tp_aggregate_percent = Column(Numeric(10, 4))
    
    risk_timer_start = Column(DateTime)
    risk_timer_expires = Column(DateTime)
    risk_eligible = Column(Boolean, default=False)
    risk_blocked = Column(Boolean, default=False)
    risk_skip_once = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime)
    
    user = relationship("User", back_populates="position_groups")
    pyramids = relationship("Pyramid", back_populates="group", cascade="all, delete-orphan")
    dca_orders = relationship("DCAOrder", back_populates="group", cascade="all, delete-orphan")
    risk_actions = relationship("RiskAction", back_populates="group", cascade="all, delete-orphan")

class Pyramid(Base):
    """
    Represents a single pyramid entry within a PositionGroup.
    """
    __tablename__ = "pyramids"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), nullable=False)
    pyramid_index = Column(Integer, nullable=False)
    
    entry_price = Column(Numeric(20, 10), nullable=False)
    entry_timestamp = Column(DateTime, nullable=False)
    signal_id = Column(String)
    
    status = Column(SQLAlchemyEnum("pending", "submitted", "filled", "cancelled", name="pyramid_status_enum"), nullable=False)
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
    
    exchange_order_id = Column(String, index=True)
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
    
    status = Column(SQLAlchemyEnum("pending", "open", "partially_filled", "filled", "cancelled", "failed", name="order_status_enum"), nullable=False, index=True)
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
