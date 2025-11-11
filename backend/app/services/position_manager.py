from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models import trading_models as models
from ..services.exchange_manager import ExchangeManager

from decimal import Decimal

class PositionGroupManager:
    def __init__(self, db: Session, exchange_manager: ExchangeManager):
        self.db = db
        self.exchange_manager = exchange_manager

    async def create_group(self, signal: Dict[str, Any], user_id: int, exchange_config_id: int) -> models.PositionGroup:
        """Create new Position Group from signal and place initial order."""
        tv_data = signal['original_payload']['tv']
        
        new_group = models.PositionGroup(
            user_id=user_id,
            exchange_config_id=exchange_config_id,
            exchange=tv_data['exchange'],
            symbol=tv_data['symbol'],
            timeframe=tv_data.get('timeframe', '1m'),
            status="waiting",  # Start as waiting
            entry_signal=signal
        )
        self.db.add(new_group)
        self.db.commit()
        self.db.refresh(new_group)

        # Create the first pyramid entry
        pyramid = self.add_pyramid(new_group.id, signal)

        # Place the initial order
        await self.place_initial_order(new_group, pyramid, signal)

        return new_group

    async def place_initial_order(self, group: models.PositionGroup, pyramid: models.Pyramid, signal: Dict[str, Any]):
        """Places the very first order for a new position group."""
        intent = signal['original_payload']['execution_intent']
        symbol = group.symbol
        side = intent['action']
        amount = Decimal(str(intent['amount']))

        try:
            order = await self.exchange_manager.place_order(
                symbol=symbol,
                side=side,
                amount=amount,
                order_type='market'
            )
            
            # Order placed successfully, update status
            group.status = "live"
            pyramid.status = "active"
            self.db.commit()
            
            # TODO: Store the order details in the database
            print(f"Successfully placed initial order for group {group.id}: {order}")

        except Exception as e:
            # If order fails, mark the group as failed
            group.status = "failed"
            pyramid.status = "failed"
            self.db.commit()
            print(f"Failed to place initial order for group {group.id}: {e}")
            # Re-raise the exception to be caught by the webhook endpoint
            raise

    def add_pyramid(self, group_id: int, signal: Dict[str, Any]) -> models.Pyramid:
        """Add pyramid to existing group"""
        new_pyramid = models.Pyramid(
            position_group_id=group_id,
            pyramid_level=1,
            status="pending"
        )
        self.db.add(new_pyramid)
        self.db.commit()
        self.db.refresh(new_pyramid)

        return new_pyramid

    def calculate_dca_orders(self, pyramid: models.Pyramid, config: Dict[str, Any]) -> List[models.DCAOrder]:
        """Generate DCA orders based on grid config"""
        # TODO: Implement DCA calculation logic
        pass

    def place_pyramid_orders(self, pyramid: models.Pyramid):
        """Submit entry + all DCA orders"""
        # TODO: Implement order placement logic
        pass

    def close_group(self, group_id: int, reason: str):
        """Close all positions and cancel orders"""
        # TODO: Implement group closing logic
        pass
