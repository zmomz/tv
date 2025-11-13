from app.models.trading_models import PositionGroup
from app.repositories.base_repository import BaseRepository


class PositionGroupRepository(BaseRepository[PositionGroup]):
    pass


position_group_repo = PositionGroupRepository(PositionGroup)
