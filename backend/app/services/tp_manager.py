from typing import Dict, Any, List, Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from ..models import trading_models as models
from ..db.session import get_db
from decimal import Decimal

class TPManager:
    def __init__(self, db: Session):
        self.db = db

    def check_per_leg_tp(self, group: models.PositionGroup) -> Optional[Dict[str, Any]]:
        """Close individual legs when TP hit"""
        for pyramid in group.pyramids:
            if pyramid.status == "open" and group.current_price >= pyramid.take_profit_price:
                pyramid.status = "closed"
                self.db.commit()
                return {
                    "group_id": group.id,
                    "pyramid_id": pyramid.id,
                    "take_profit_price": pyramid.take_profit_price,
                    "current_price": group.current_price
                }
        return None

    def check_aggregate_tp(self, group: models.PositionGroup) -> Optional[Dict[str, Any]]:
        """Close entire group when avg TP hit"""
        # TODO: Implement aggregate TP logic
        return None

    def check_hybrid_tp(self, group: models.PositionGroup) -> Optional[Dict[str, Any]]:
        """Run both, first trigger wins"""
        # TODO: Implement hybrid TP logic
        return None

def get_tp_manager(db: Session = Depends(get_db)) -> TPManager:
    return TPManager(db)
