import uuid
from sqlalchemy import Column, String, DateTime, func, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB
from ..db.base import Base

PositionGroupStatus = ENUM("pending", "active", "closed", "error", name="position_group_status")
PyramidStatus = ENUM("pending", "active", "filled", "error", name="pyramid_status")
DCAOrderStatus = ENUM("pending", "open", "filled", "canceled", "error", name="dca_order_status")

class PositionGroup(Base):
    __tablename__ = "position_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exchange_config_id = Column(UUID(as_uuid=True), ForeignKey("exchange_configs.id"), nullable=False)
    symbol = Column(String, nullable=False)
    status = Column(PositionGroupStatus, default="pending")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Pyramid(Base):
    __tablename__ = "pyramids"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), nullable=False)
    pyramid_number = Column(Integer, nullable=False)
    status = Column(PyramidStatus, default="pending")
    created_at = Column(DateTime, default=func.now())

class DCAOrder(Base):
    __tablename__ = "dca_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pyramid_id = Column(UUID(as_uuid=True), ForeignKey("pyramids.id"), nullable=False)
    order_number = Column(Integer, nullable=False)
    order_id = Column(String)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    status = Column(DCAOrderStatus, default="pending")
    created_at = Column(DateTime, default=func.now())
    filled_at = Column(DateTime)

class QueueEntry(Base):
    __tablename__ = "queue_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    payload = Column(JSONB)
    priority = Column(Float, default=0.0)
    queued_at = Column(DateTime, default=func.now())