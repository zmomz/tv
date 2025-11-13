from ..models.trading_models import PositionGroup, PositionGroupStatus
from ..db.session import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends # Import Depends
from ..core.config import settings
from uuid import UUID
from sqlalchemy import select, func

class ExecutionPoolManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_open_slots(self, user_id: UUID) -> int:
        """
        Count available slots
        """
        max_open_groups = settings.POOL_MAX_OPEN_GROUPS
        result = await self.db.execute(
            select(func.count())
            .where(
                PositionGroup.user_id == user_id,
                PositionGroup.status == PositionGroupStatus.LIVE
            )
        )
        open_positions_count = result.scalar_one()
        return max_open_groups - open_positions_count

    async def can_open_position(self, user_id: UUID) -> bool:
        """
        Check if a new position can be opened.
        """
        open_slots = await self.get_open_slots(user_id)
        return open_slots > 0

    async def consume_slot(self, group: PositionGroup):
        """
        Mark a slot as consumed.
        """
        # This might involve updating the status of the position group
        # or other logic to reflect a slot being used.
        pass

    async def release_slot(self, group: PositionGroup):
        """
        Mark a slot as released.
        """
        # This might involve updating the status of the position group
        # or other logic to reflect a slot being freed.
        pass

def get_pool_manager(db: AsyncSession = Depends(get_async_db)) -> ExecutionPoolManager:
    return ExecutionPoolManager(db)
