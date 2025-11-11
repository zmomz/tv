import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Integer, Text, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSON
from ..db.base import Base
import sqlalchemy as sa

class RiskAnalysis(Base):
    __tablename__ = "risk_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    losing_position_group_id = Column(UUID(as_uuid=True), ForeignKey("position_groups.id"), nullable=False)
    winning_position_group_ids = Column(JSON, nullable=False)
    required_usd_to_cover = Column(DECIMAL(20, 8), nullable=False)
    realized_profit_usd = Column(DECIMAL(20, 8), nullable=False)
    action_taken = Column(String(255), nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)