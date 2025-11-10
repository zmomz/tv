from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from ..db.base import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exchange = Column(String, nullable=False)
    encrypted_api_key = Column(String, nullable=False)
    encrypted_secret = Column(String, nullable=False)
    is_testnet = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    position_groups = relationship("PositionGroup", back_populates="api_key_rel")

class PositionGroup(Base):
    __tablename__ = "position_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    pair = Column(String, index=True, nullable=False)
    timeframe = Column(String, nullable=False)
    status = Column(String, default="open", nullable=False) # e.g., "open", "closed", "liquidated"
    avg_entry_price = Column(Float, nullable=True)
    unrealized_pnl_percent = Column(Float, default=0.0)
    unrealized_pnl_usd = Column(Float, default=0.0)
    tp_mode = Column(String, nullable=True) # e.g., "per_leg", "aggregate", "hybrid"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    last_pyramid_at = Column(DateTime(timezone=True), nullable=True)

    api_key_rel = relationship("APIKey", back_populates="position_groups")
    pyramids = relationship("Pyramid", back_populates="position_group")

class Pyramid(Base):
    __tablename__ = "pyramids"

    id = Column(Integer, primary_key=True, index=True)
    position_group_id = Column(Integer, ForeignKey("position_groups.id"), nullable=False)
    entry_price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    position_group = relationship("PositionGroup", back_populates="pyramids")
    dca_legs = relationship("DCALeg", back_populates="pyramid")

class DCALeg(Base):
    __tablename__ = "dca_legs"

    id = Column(Integer, primary_key=True, index=True)
    pyramid_id = Column(Integer, ForeignKey("pyramids.id"), nullable=False)
    price_gap = Column(Float, nullable=False)
    capital_weight = Column(Float, nullable=False)
    tp_target = Column(Float, nullable=True)
    fill_price = Column(Float, nullable=True)
    status = Column(String, default="pending", nullable=False) # e.g., "pending", "filled", "cancelled", "tp_hit"
    order_id = Column(String, nullable=True)
    filled_at = Column(DateTime(timezone=True), nullable=True)

    pyramid = relationship("Pyramid", back_populates="dca_legs")

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
