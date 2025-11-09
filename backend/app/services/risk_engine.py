from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import models
from app.core.config import settings
from sqlalchemy import desc, asc

class RiskEngine:
    def __init__(self, db: Session):
        self.db = db

    def should_activate(self, group: models.PositionGroup) -> bool:
        """Check: 5 pyramids + timer + loss threshold"""
        if group.unrealized_pnl_percent is not None and group.unrealized_pnl_percent < settings.RISK_LOSS_THRESHOLD_PERCENT:
            # For now, only check loss threshold. Other conditions (pyramids, timer) will be added later.
            return True
        return False

    def select_losing_group(self, user_id: int) -> Optional[models.PositionGroup]:
        """Rank by loss %, then loss USD, then age"""
        losing_groups = self.db.query(models.PositionGroup).filter(
            models.PositionGroup.user_id == user_id,
            models.PositionGroup.status == "Live",
            models.PositionGroup.unrealized_pnl_percent < settings.RISK_LOSS_THRESHOLD_PERCENT
        ).order_by(
            asc(models.PositionGroup.unrealized_pnl_percent), # Most negative PnL percent first
            asc(models.PositionGroup.unrealized_pnl_usd),    # Most negative PnL USD first
            asc(models.PositionGroup.created_at)             # Oldest first
        ).first()
        return losing_groups

    def calculate_required_usd(self, group: models.PositionGroup) -> float:
        """Get absolute unrealized loss"""
        if group.unrealized_pnl_usd is not None and group.unrealized_pnl_usd < 0:
            return abs(group.unrealized_pnl_usd)
        return 0.0

    def select_winning_groups(self, user_id: int, required_usd: float) -> List[models.PositionGroup]:
        """Pick up to 3 winners by profit USD"""
        winning_groups = self.db.query(models.PositionGroup).filter(
            models.PositionGroup.user_id == user_id,
            models.PositionGroup.status == "Live",
            models.PositionGroup.unrealized_pnl_usd > 0  # Only consider groups with profit
        ).order_by(
            desc(models.PositionGroup.unrealized_pnl_usd) # Most profitable first
        ).limit(3).all()
        return winning_groups
