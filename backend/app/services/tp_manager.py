from typing import Dict, Any, List, Optional
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import trading_models as models
from ..db.session import get_async_db
from decimal import Decimal

class TPManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_per_leg_tp(self, group: models.PositionGroup) -> Optional[Dict[str, Any]]:
        """Close individual legs when TP hit"""
        result = await self.db.execute(
            select(models.Pyramid).where(
                models.Pyramid.group_id == group.id,
                models.Pyramid.status == "open"
            )
        )
        pyramids = (await result).scalars().all()

        for pyramid in pyramids:
            # Assuming group.current_price is fetched and available
            if group.current_price >= pyramid.take_profit_price:
                pyramid.status = "closed"
                self.db.add(pyramid)
                await self.db.commit()
                return {
                    "group_id": group.id,
                    "pyramid_id": pyramid.id,
                    "take_profit_price": pyramid.take_profit_price,
                    "current_price": group.current_price
                }
        return None

    async def check_aggregate_tp(self, group: models.PositionGroup) -> Optional[Dict[str, Any]]:
        """Close entire group when avg TP hit"""
        # TODO: Implement aggregate TP logic
        return None

    async def check_hybrid_tp(self, group: models.PositionGroup) -> Optional[Dict[str, Any]]:
        """Run both, first trigger wins"""
        # TODO: Implement hybrid TP logic
        return None

def get_tp_manager(db: AsyncSession = Depends(get_async_db)) -> TPManager:
    return TPManager(db)