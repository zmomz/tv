from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.trading_models import PositionGroup, Pyramid
from uuid import UUID
from fastapi import Depends
from ..db.session import get_async_db
from decimal import Decimal
from datetime import datetime
from ..core.config import settings
from .order_service import place_partial_close_order
from ..models.risk_analytics_models import RiskAction

class RiskEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_risk_conditions(self) -> None:
        """
        Evaluate risk conditions and execute mitigation strategies.
        """
        # This is a placeholder. In a real-world application, you would
        # query the database for all live position groups, and then
        # evaluate the risk conditions for each one.
        pass

    async def should_activate_risk_engine(self, position_group: PositionGroup, unrealized_pnl_percent: Decimal) -> bool:
        """
        Determine whether the risk engine should be activated for a position_group.
        Activation conditions from SoW 4.2:
        - All 5 pyramids received.
        - Post-full waiting time has passed.
        - Loss percent is below the threshold.
        - It must also respect the `timer_start_condition` from the config.
        """
        # 1. Check if all 5 pyramids are received (if required by config)
        if settings.RISK_REQUIRE_FULL_PYRAMIDS:
            result = await self.db.execute(
                select(func.count())
                .select_from(Pyramid)
                .where(Pyramid.group_id == position_group.id)
            )
            pyramid_count = (await result).scalar_one()
            if pyramid_count < 5:
                return False

        # 2. Check if loss percent is below the threshold
        if unrealized_pnl_percent > settings.RISK_LOSS_THRESHOLD_PERCENT:
            return False

        # 3. Check post-full waiting time (implicitly assuming 'pyramid_full' as timer_start_condition)
        if settings.RISK_POST_FULL_WAIT_MINUTES > 0:
            # Find the creation time of the last pyramid entry
            result = await self.db.execute(
                select(Pyramid)
                .where(Pyramid.group_id == position_group.id)
                .order_by(Pyramid.entry_timestamp.desc())
            )
            last_pyramid = (await result).scalars().first()

            if last_pyramid:
                wait_time_seconds = settings.RISK_POST_FULL_WAIT_MINUTES * 60
                time_since_last_pyramid = (datetime.utcnow() - last_pyramid.entry_timestamp).total_seconds()
                if time_since_last_pyramid < wait_time_seconds:
                    return False
            else:
                return False

        return True

    async def find_losing_positions(self, user_id: UUID) -> list[PositionGroup]:
        """
        Find all losing positions for a user, ranked by priority for risk mitigation.
        Ranking rules: 1) highest loss percent, 2) highest unrealized dollar loss, 3) oldest trade.
        """
        result = await self.db.execute(
            select(PositionGroup).where(
                PositionGroup.user_id == user_id,
                PositionGroup.status == "active",
                PositionGroup.unrealized_pnl_percent < 0
            )
        )
        losing_positions = (await result).scalars().all()

        sorted_losing_positions = sorted(
            losing_positions,
            key=lambda pg: (pg.unrealized_pnl_percent, pg.unrealized_pnl_usd, pg.created_at),
            reverse=False
        )

        return sorted_losing_positions

    async def find_winning_positions(self, user_id: UUID) -> list[PositionGroup]:
        """
        Find all winning positions for a user, ranked by highest profit in USD.
        """
        result = await self.db.execute(
            select(PositionGroup).where(
                PositionGroup.user_id == user_id,
                PositionGroup.status == "active",
                PositionGroup.unrealized_pnl_usd > 0
            )
        )
        winning_positions = (await result).scalars().all()

        sorted_winning_positions = sorted(
            winning_positions,
            key=lambda pg: pg.unrealized_pnl_usd,
            reverse=True
        )

        return sorted_winning_positions

    async def execute_risk_mitigation(
        self, losing_position: PositionGroup, winning_positions: list[PositionGroup]
    ) -> None:
        """
        Execute a risk mitigation strategy by partially closing winning positions
        to cover the losses of a losing position.
        """
        required_usd = abs(losing_position.unrealized_pnl_usd)
        realized_profit = Decimal("0.0")
        winning_positions_used = []

        for winner in winning_positions:
            if realized_profit >= required_usd:
                break

            profit_to_realize = min(required_usd - realized_profit, winner.unrealized_pnl_usd)
            
            await place_partial_close_order(
                db=self.db,
                position_group=winner,
                usd_amount_to_realize=profit_to_realize
            )
            
            realized_profit += profit_to_realize
            winning_positions_used.append(winner)

        # Log the operation
        risk_action_entry = RiskAction(
            group_id=losing_position.id,
            action_type="offset_loss",
            loser_group_id=losing_position.id,
            loser_pnl_usd=losing_position.unrealized_pnl_usd,
            winner_details=[{"group_id": str(w.id), "pnl_usd": str(w.unrealized_pnl_usd)} for w in winning_positions_used],
            notes="Partial close of winning positions to cover loss."
        )
        self.db.add(risk_action_entry)

def get_risk_engine(db: AsyncSession = Depends(get_async_db)) -> RiskEngine:
    return RiskEngine(db)
