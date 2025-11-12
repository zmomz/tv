from sqlalchemy.orm import Session
from ..models.trading_models import PositionGroup

def get_dashboard_stats(db: Session):
    """
    Get dashboard statistics.
    """
    open_positions = db.query(PositionGroup).filter(PositionGroup.status == "open").count()
    total_positions = db.query(PositionGroup).count()
    pnl = 0  # TODO: Calculate PnL
    return {
        "open_positions": open_positions,
        "total_positions": total_positions,
        "pnl": pnl,
    }
