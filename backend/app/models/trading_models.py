import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from ..db.base import Base

class PositionGroupStatus(enum.Enum):
    open = "open"
    closed = "closed"
    failed = "failed"

class PyramidStatus(enum.Enum):
    pending = "pending"
    open = "open"
    closed = "closed"
    failed = "failed"

class DCAOrderStatus(enum.Enum):
    pending = "pending"
    open = "open"
    filled = "filled"
    cancelled = "cancelled"
    failed = "failed"

class PositionGroup(Base):
    __tablename__ = 'position_groups'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    exchange_config_id = Column(UUID(as_uuid=True), ForeignKey('exchange_configs.id'), nullable=True)
    exchange = Column(String)
    symbol = Column(String, nullable=False)
    timeframe = Column(String)
    status = Column(Enum(PositionGroupStatus), default=PositionGroupStatus.open)
    unrealized_pnl_percent = Column(Float)
    unrealized_pnl_usd = Column(Float)
    entry_signal = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    pyramids = relationship("Pyramid", back_populates="position_group", cascade="all, delete-orphan")

class Pyramid(Base):
    __tablename__ = 'pyramids'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_group_id = Column(UUID(as_uuid=True), ForeignKey('position_groups.id'), nullable=False)
    pyramid_level = Column(Integer)
    status = Column(Enum(PyramidStatus), default=PyramidStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    position_group = relationship("PositionGroup", back_populates="pyramids")
    dca_orders = relationship("DCAOrder", back_populates="pyramid", cascade="all, delete-orphan")

class DCAOrder(Base):
    __tablename__ = 'dca_orders'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_group_id = Column(UUID(as_uuid=True), ForeignKey('position_groups.id'), nullable=False)
    pyramid_id = Column(UUID(as_uuid=True), ForeignKey('pyramids.id'), nullable=False)
    pyramid_level = Column(Integer)
    dca_level = Column(Integer)
    exchange_order_id = Column(String)
    price_gap_percent = Column(Float)
    capital_weight = Column(Float)
    tp_target_percent = Column(Float)
    status = Column(Enum(DCAOrderStatus), default=DCAOrderStatus.pending)
    price = Column(Float)
    expected_price = Column(Float)
    quantity = Column(Float)
    filled_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    pyramid = relationship("Pyramid", back_populates="dca_orders")

class QueueEntry(Base):
    __tablename__ = 'queue_entries'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    exchange = Column(String)
    symbol = Column(String, nullable=False)
    timeframe = Column(String)
    priority_score = Column(Integer, default=0)
    replacement_count = Column(Integer, default=0)
    signal = Column(JSON)
    original_signal = Column(JSON)
    status = Column(String, default="queued")
    created_at = Column(DateTime, default=datetime.utcnow)