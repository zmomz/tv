from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models import models
from app.core.config import settings

class ExecutionPoolManager:
    def __init__(self, db: Session):
        self.db = db

    def get_open_slots(self, user_id: int) -> int:
        """Count available slots"""
        max_open_groups = settings.POOL_MAX_OPEN_GROUPS
        open_groups_count = self.db.query(models.PositionGroup).filter(
            models.PositionGroup.user_id == user_id,
            models.PositionGroup.status == "Live"
        ).count()
        return max_open_groups - open_groups_count

    def can_open_position(self, user_id: int) -> bool:
        """Check if new group allowed"""
        return self.get_open_slots(user_id) > 0

    def consume_slot(self, group: models.PositionGroup):
        """Mark slot as used"""
        # In our current model, creating a PositionGroup already marks it as 'Live',
        # which is counted by get_open_slots. No explicit action needed here beyond creation.
        pass

    def release_slot(self, group_id: int):
        """Free slot when group closes"""
        # This will be handled when a PositionGroup's status changes from 'Live'
        pass
