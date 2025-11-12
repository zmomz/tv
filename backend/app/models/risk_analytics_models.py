import uuid
from sqlalchemy import Column, String, DateTime, func, ForeignKey, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from ..db.base import Base

class RiskAction(Base):
    __tablename__ = "risk_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    loser_group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), nullable=False)
    winner_group_ids = Column(JSONB) # List of winner group IDs
    action_type = Column(String) # e.g., "OFFSET_LOSS"
    details = Column(Text)
    timestamp = Column(DateTime, default=func.now())

