from ..models.trading_models import PositionGroup
from sqlalchemy.orm import Session
from uuid import UUID
from ..core.config import settings
from fastapi import Depends
from ..db.session import get_db

class ExecutionPoolManager:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_open_slots(self, user_id: UUID) -> int:
        """
        Count available slots
        """
        max_open_groups = settings.POOL_MAX_OPEN_GROUPS
        return self.db.query(PositionGroup).filter(
            PositionGroup.user_id == user_id,
            PositionGroup.status == "open",
        ).count()

    def can_open_position(self, user_id: UUID) -> bool:
        """
        Check if a new position can be opened.
        """
        return self.get_open_slots(user_id) > 0

    def consume_slot(self, group: PositionGroup):
        """
        Mark a slot as consumed.
        """
        pass

    def release_slot(self, group: PositionGroup):
        """
        Mark a slot as released.
        """
        pass

def get_pool_manager(db: Session = Depends(get_db)) -> ExecutionPoolManager:
    return ExecutionPoolManager(db)