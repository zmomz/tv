from sqlalchemy import (Column, String, DateTime, JSON, ForeignKey, Enum as SQLAlchemyEnum, Numeric)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from decimal import Decimal
from ..db.base import Base

class RiskAction(Base):
    """
    Records actions taken by the Risk Engine.
    """
    __tablename__ = "risk_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), nullable=False)
    
    action_type = Column(SQLAlchemyEnum("offset_loss", "manual_block", "manual_skip", name="risk_action_type_enum"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Details for offset_loss
    loser_group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"))
    loser_pnl_usd = Column(Numeric(20, 10))
    
    # Details for winners (JSON array of {group_id, pnl_usd, quantity_closed})
    winner_details = Column(JSON)
    
    notes = Column(String)
    
    group = relationship("PositionGroup", foreign_keys=[group_id], back_populates="risk_actions")

