from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models.trading_models import PositionGroup, DCAOrder
from ..services import exchange_manager
from decimal import Decimal
from typing import List

async def check_take_profit_conditions() -> None:
    """
    Check for take-profit conditions and execute orders.
    """
    # This is a placeholder. In a real-world application, you would
    # query the database for all live position groups, and then check
    # their take-profit conditions.
    pass

async def execute_per_leg_tp(db: Session, position_group: PositionGroup) -> None:
    """
    Execute take-profit orders for each filled DCA leg that has met its target.
    """
    # Get only the orders that are filled and could potentially be sold
    result = await db.execute(
        select(DCAOrder).where(
            DCAOrder.group_id == position_group.id,
            DCAOrder.status == "filled"
        )
    )
    orders_to_check = (await result).scalars().all()

    if not orders_to_check:
        return

    orders_updated = False
    async with await exchange_manager.get_exchange(db, position_group.exchange, position_group.user_id) as manager:
        current_price = await manager.get_current_price(position_group.symbol)
        
        tp_config = position_group.tp_config
        price_targets_pct = tp_config["tp_price_targets"]

        for order in orders_to_check:
            # Ensure we don't try to access a price target that doesn't exist
            if order.dca_level < len(price_targets_pct):
                tp_multiplier = price_targets_pct[order.dca_level]
                # Assuming long position for now
                # In a real scenario, you'd check the position side
                target_price = order.filled_price * tp_multiplier

                if current_price >= target_price:
                    await manager.place_order(
                        symbol=position_group.symbol,
                        side="sell",
                        order_type="market",
                        amount=order.quantity
                    )
                    order.status = "tp-taken"
                    db.add(order)
                    orders_updated = True
    
    if orders_updated:
        db.commit()

def calculate_average_entry_price(orders: List[DCAOrder]) -> Decimal:
    """
    Calculates the weighted average entry price for a list of DCA orders.
    """
    total_quantity = Decimal("0.0")
    total_cost = Decimal("0.0")

    for order in orders:
        if order.status == "filled" and order.filled_price and order.quantity:
            total_quantity += order.quantity
            total_cost += order.filled_price * order.quantity
    
    if total_quantity == Decimal("0.0"):
        return Decimal("0.0") # Avoid division by zero

    return total_cost / total_quantity

async def execute_aggregate_tp(db: Session, position_group: PositionGroup) -> None:
    """
    Execute a take-profit order for the entire position group.
    """
    result = await db.execute(
        select(DCAOrder).where(
            DCAOrder.group_id == position_group.id,
            DCAOrder.status == "filled"
        )
    )
    orders_to_check = (await result).scalars().all()

    if not orders_to_check:
        return

    average_entry_price = calculate_average_entry_price(orders_to_check)
    if average_entry_price == Decimal("0.0"):
        return # No filled orders or zero average entry price

    async with await exchange_manager.get_exchange(db, position_group.exchange, position_group.user_id) as manager:
        current_price = await manager.get_current_price(position_group.symbol)

        tp_config = position_group.tp_config
        # Assuming only one aggregate target for simplicity as per test setup
        tp_multiplier = tp_config["tp_price_targets"][0]

        target_price = average_entry_price * tp_multiplier

        if current_price >= target_price:
            total_quantity = sum([order.quantity for order in orders_to_check if order.status == "filled"], Decimal("0.0"))
            if total_quantity > Decimal("0.0"):
                await manager.place_order(
                    symbol=position_group.symbol,
                    side="sell",
                    order_type="market",
                    amount=total_quantity
                )
                position_group.status = "closed" # Mark position group as closed
                db.add(position_group)
                db.commit()

async def execute_hybrid_tp(db: Session, position_group: PositionGroup) -> None:
    """
    Execute take-profit orders using a hybrid strategy.
    This implementation closes a percentage of the position if the aggregate profit target is met.
    """
    result = await db.execute(
        select(DCAOrder).where(
            DCAOrder.group_id == position_group.id,
            DCAOrder.status == "filled"
        )
    )
    orders_to_check = (await result).scalars().all()

    if not orders_to_check:
        return

    average_entry_price = calculate_average_entry_price(orders_to_check)
    if average_entry_price == Decimal("0.0"):
        return # No filled orders or zero average entry price

    tp_config = position_group.tp_config
    aggregate_profit_target = tp_config.get("aggregate_profit_target")
    partial_close_percentage = tp_config.get("partial_close_percentage")

    if not aggregate_profit_target or not partial_close_percentage:
        return # Hybrid config missing

    async with await exchange_manager.get_exchange(db, position_group.exchange, position_group.user_id) as manager:
        current_price = await manager.get_current_price(position_group.symbol)

        target_price = average_entry_price * aggregate_profit_target

        if current_price >= target_price:
            total_quantity = sum([order.quantity for order in orders_to_check if order.status == "filled"], Decimal("0.0"))
            if total_quantity > Decimal("0.0"):
                quantity_to_close = total_quantity * partial_close_percentage
                
                await manager.place_order(
                    symbol=position_group.symbol,
                    side="sell",
                    order_type="market",
                    amount=quantity_to_close
                )
                # Update position group status to reflect partial closure
                position_group.status = "partially-closed" # Or a more granular status
                db.add(position_group)
                db.commit()
