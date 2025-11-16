from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.trading_models import PositionGroup, PositionGroupStatus

async def get_dashboard_stats(db: AsyncSession):
    """
    Get dashboard statistics asynchronously.
    """
    open_positions_result = await db.execute(
        select(func.count(PositionGroup.id)).where(PositionGroup.status == PositionGroupStatus.LIVE)
    )
    open_positions = open_positions_result.scalar_one()

    total_positions_result = await db.execute(select(func.count(PositionGroup.id)))
    total_positions = total_positions_result.scalar_one()

    pnl_result = await db.execute(
        select(func.sum(PositionGroup.realized_pnl_usd + PositionGroup.unrealized_pnl_usd))
    )
    pnl = pnl_result.scalar_one_or_none() or 0

    return {
        "open_positions": open_positions,
        "total_positions": total_positions,
        "pnl": pnl,
    }
