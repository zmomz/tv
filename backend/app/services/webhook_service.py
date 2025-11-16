from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.trading_models import PositionGroup, PositionGroupStatus
from ..services.queue_service import add_to_queue
from ..core.config import settings
from uuid import UUID
from typing import Dict, Any
from decimal import Decimal

async def process_webhook_signal(db: AsyncSession, user_id: UUID, tv_data: Dict[str, Any], execution_intent: Dict[str, Any]):
    """
    Processes a webhook signal by checking the user's execution pool.
    If the pool is full, the signal is queued. Otherwise, a new position group is created.
    """
    # 1. Check the number of currently live positions for the user.
    live_positions_query = select(func.count(PositionGroup.id)).filter(
        PositionGroup.user_id == user_id,
        PositionGroup.status == PositionGroupStatus.LIVE
    )
    result = await db.execute(live_positions_query)
    live_positions_count = result.scalar_one()

    # 2. Compare with the pool size from settings.
    if live_positions_count >= settings.POOL_MAX_OPEN_GROUPS:
        # Pool is full, add the signal to the queue.
        queued_signal = await add_to_queue(db, tv_data, user_id)
        return {"status": "success", "action": "queued", "queued_signal_id": queued_signal.id}
    else:
        # Pool has space, create a new position group.
        position_group = await create_position_group_from_signal(db, tv_data, user_id)
        return {"status": "success", "action": "created", "position_group_id": position_group.id}

async def create_position_group_from_signal(db: AsyncSession, signal: Dict[str, Any], user_id: UUID) -> PositionGroup:
    """
    Create a new position group from a signal.
    """
    db_position_group = PositionGroup(
        user_id=user_id,
        exchange=signal["exchange"],
        symbol=signal["symbol"],
        timeframe=int(signal["timeframe"].replace("m", "")),
        status=PositionGroupStatus.WAITING,
        entry_signal=signal,
        total_dca_legs=5, # Placeholder
        base_entry_price=Decimal("0.0"), # Placeholder
        weighted_avg_entry=Decimal("0.0"), # Placeholder
        tp_mode="per_leg", # Placeholder
        side="long" # Placeholder
    )
    db.add(db_position_group)
    await db.commit()
    await db.refresh(db_position_group)
    return db_position_group
