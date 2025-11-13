from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models.trading_models import PositionGroup, DCAOrder
from ..services import exchange_manager, grid_calculator, validation_service
from uuid import UUID
from decimal import Decimal

async def place_dca_orders(db: Session, position_group: PositionGroup) -> List[DCAOrder]:
    """
    Place DCA orders for a position group.
    """
    dca_config = position_group.entry_signal["dca_config"]
    dca_levels = grid_calculator.calculate_dca_levels(
        Decimal(position_group.entry_signal["entry_price"]),
        dca_config,
    )
    dca_sizes = grid_calculator.calculate_position_size(
        Decimal(position_group.entry_signal["total_risk_usd"]),
        dca_config["dca_weights"],
    )
    
    orders = []
    async with await exchange_manager.get_exchange(db, position_group.exchange, position_group.user_id) as manager:
        for i, level in enumerate(dca_levels):
            quantity, price = await validation_service.validate_and_adjust_order(
                db,
                position_group.exchange,
                position_group.symbol,
                "buy",
                dca_sizes[i] / level["price"],
                level["price"],
            )
            
            order = await manager.place_order(
                symbol=position_group.symbol,
                side="buy",
                order_type="limit",
                amount=quantity,
                price=price,
            )
            
            db_order = DCAOrder(
                group_id=position_group.id,
                leg_index=i,
                quantity=quantity,
                status="pending",
                exchange_order_id=order["id"],
            )
            db.add(db_order)
            orders.append(db_order)
        
    db.commit()
    return orders

async def monitor_order_fills(db: Session) -> None:
    """
    Monitor for filled orders and update the database.
    """
    result = await db.execute(
        select(DCAOrder).where(DCAOrder.status == "pending")
    )
    pending_orders = (await result).scalars().all()
    # Group orders by user and exchange to minimize API calls
    exchange_groups = {}
    for order in pending_orders:
        key = (order.position_group.user_id, order.position_group.exchange)
        if key not in exchange_groups:
            exchange_groups[key] = []
        exchange_groups[key].append(order)

    for (user_id, exchange_name), orders_in_group in exchange_groups.items():
        async with await exchange_manager.get_exchange(db, exchange_name, user_id) as manager:
            for order in orders_in_group:
                try:
                    exchange_order = await manager.fetch_order(
                        order_id=order.exchange_order_id,
                        symbol=order.position_group.symbol
                    )
                    if exchange_order and exchange_order["status"] == "closed": # 'closed' typically means filled in ccxt
                        await handle_filled_order(db, order, exchange_order)
                except Exception as e:
                    # Log the error, but don't stop monitoring other orders
                    print(f"Error fetching order {order.exchange_order_id}: {e}")

async def place_partial_close_order(db: Session, position_group: PositionGroup, usd_amount_to_realize: Decimal):
    """
    Placeholder for placing a partial closing order.
    """
    pass

async def handle_filled_order(db: Session, dca_order: DCAOrder, fill_data: dict) -> None:
    """
    Handle a filled order.
    """
    dca_order.status = "filled"
    dca_order.filled_price = Decimal(fill_data["price"])
    dca_order.filled_quantity = Decimal(fill_data["filled"])
    await db.commit()

async def cancel_pending_orders(db: Session, position_group_id: UUID) -> None:
    """
    Cancel all pending orders for a position group.
    """
    result = await db.execute(
        select(DCAOrder).where(
            DCAOrder.group_id == position_group_id,
            DCAOrder.status == "pending"
        )
    )
    orders = (await result).scalars().all()    
    if orders:
        # Assuming all orders in a position group are for the same exchange and user
        position_group = orders[0].position_group
        async with await exchange_manager.get_exchange(db, position_group.exchange, position_group.user_id) as manager:
            for order in orders:
                await manager.cancel_order(
                    symbol=order.position_group.symbol,
                    order_id=order.exchange_order_id,
                )
                order.status = "cancelled"
            
        db.commit()
