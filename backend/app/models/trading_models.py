import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Integer, Text, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSON
from ..db.base import Base

class PositionGroup(Base):
    __tablename__ = "position_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    status = Column(Enum('waiting', 'live', 'partially_filled', 'closing', 'closed', name='position_group_status'), nullable=False)
    entry_signal = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class DCAOrder(Base):
    __tablename__ = "dca_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), nullable=False)
    pyramid_level = Column(Integer, nullable=False)
    dca_level = Column(Integer, nullable=False)
    expected_price = Column(DECIMAL(20, 8), nullable=False)
    quantity = Column(DECIMAL(20, 8), nullable=False)
    filled_price = Column(DECIMAL(20, 8), nullable=True)
    filled_quantity = Column(DECIMAL(20, 8), nullable=True)
    status = Column(Enum('pending', 'filled', 'cancelled', 'failed', name='dca_order_status'), nullable=False)
    exchange_order_id = Column(String(100), nullable=True)

class Pyramid(Base):
    __tablename__ = "pyramids"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), nullable=False)
    pyramid_level = Column(Integer, nullable=False)
    status = Column(Enum('pending', 'active', 'closed', name='pyramid_status'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class DCALeg(Base):
    __tablename__ = "dca_legs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dca_order_id = Column(UUID(as_uuid=True), ForeignKey("dca_orders.id"), nullable=False)
    leg_number = Column(Integer, nullable=False)
    status = Column(Enum('pending', 'filled', 'cancelled', 'failed', name='dca_leg_status'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
