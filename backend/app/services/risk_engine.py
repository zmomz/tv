from sqlalchemy.orm import Session
from ..models.trading_models import PositionGroup, Pyramid
from uuid import UUID
from fastapi import Depends
from ..db.session import get_db
from decimal import Decimal
from datetime import datetime
from ..core.config import settings
from .order_service import place_partial_close_order
from ..models.risk_analytics_models import RiskAnalysis

class RiskEngine:
    def __init__(self, db: Session):
        self.db = db

    def evaluate_risk_conditions(self) -> None:
        """
        Evaluate risk conditions and execute mitigation strategies.
        """
        # This is a placeholder. In a real-world application, you would
        # query the database for all live position groups, and then
        # evaluate the risk conditions for each one.
        pass

    def should_activate_risk_engine(self, position_group: PositionGroup, unrealized_pnl_percent: Decimal) -> bool:
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
            pyramid_count = self.db.query(Pyramid).filter(Pyramid.position_group_id == position_group.id).count()
            if pyramid_count < 5:
                return False

        # 2. Check if loss percent is below the threshold
        if unrealized_pnl_percent > settings.RISK_LOSS_THRESHOLD_PERCENT:
            return False

        # 3. Check post-full waiting time (implicitly assuming 'pyramid_full' as timer_start_condition)
        if settings.RISK_POST_FULL_WAIT_MINUTES > 0:
            # Find the creation time of the last pyramid entry
            last_pyramid = self.db.query(Pyramid).filter(
                Pyramid.position_group_id == position_group.id
            ).order_by(Pyramid.created_at.desc()).first()

            if last_pyramid:
                wait_time_seconds = settings.RISK_POST_FULL_WAIT_MINUTES * 60
                time_since_last_pyramid = (datetime.utcnow() - last_pyramid.created_at).total_seconds()
                if time_since_last_pyramid < wait_time_seconds:
                    return False
            else:
                # If RISK_REQUIRE_FULL_PYRAMIDS is False and no pyramids exist, this condition might be skipped
                # For now, if no pyramids and wait time is required, return False.
                # This logic might need refinement based on exact SoW interpretation for edge cases.
                return False

        return True

    async def find_losing_positions(self, user_id: UUID) -> list[PositionGroup]:
        """
        Find all losing positions for a user, ranked by priority for risk mitigation.
        Ranking rules: 1) highest loss percent, 2) highest unrealized dollar loss, 3) oldest trade.
        """
        # Query for live losing positions
        losing_positions = self.db.query(PositionGroup).filter(
            PositionGroup.user_id == user_id,
            PositionGroup.status == "live",
            PositionGroup.unrealized_pnl_percent < 0  # Only consider losing positions
        ).all()

        # Sort by priority rules: highest loss percent (most negative), highest unrealized dollar loss (most negative), oldest trade
        # Python's sort is stable, so we can sort by multiple keys in reverse order of importance
        # For loss percent and USD loss, we want the *most negative* first, so we sort ascending on the absolute value, or descending on the negative value.
        # For created_at, oldest first is ascending.
        sorted_losing_positions = sorted(losing_positions,
                                         key=lambda pg: (pg.unrealized_pnl_percent, pg.unrealized_pnl_usd, pg.created_at),
                                         reverse=False) # Sort ascending for percent and USD loss (most negative first), then ascending for created_at

        return sorted_losing_positions

    async def find_winning_positions(self, user_id: UUID) -> list[PositionGroup]:
        """
        Find all winning positions for a user, ranked by highest profit in USD.
        """
        # Query for live winning positions
        winning_positions = self.db.query(PositionGroup).filter(
            PositionGroup.user_id == user_id,
            PositionGroup.status == "live",
            PositionGroup.unrealized_pnl_percent > 0  # Only consider winning positions
        ).all()

        # Sort by highest unrealized dollar profit (descending)
        sorted_winning_positions = sorted(winning_positions,
                                          key=lambda pg: pg.unrealized_pnl_usd,
                                          reverse=True)

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
            
            # This is a simplified assumption. In reality, you'd need to calculate the
            # exact quantity to sell to realize this profit, which is complex.
            # For now, we'll assume a direct mapping for the purpose of the test.
            await place_partial_close_order(
                db=self.db,
                position_group=winner,
                usd_amount_to_realize=profit_to_realize
            )
            
            realized_profit += profit_to_realize
            winning_positions_used.append(winner.id)

        # Log the operation
        risk_analysis_entry = RiskAnalysis(
            user_id=losing_position.user_id,
            losing_position_group_id=losing_position.id,
            winning_position_group_ids=[str(uuid) for uuid in winning_positions_used],
            required_usd_to_cover=required_usd,
            realized_profit_usd=realized_profit,
            action_taken="Partial close of winning positions to cover loss.",
            details={}
        )
        self.db.add(risk_analysis_entry)
        self.db.commit()

def get_risk_engine(db: Session = Depends(get_db)) -> RiskEngine:
    return RiskEngine(db)
