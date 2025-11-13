from app.models.risk_analytics_models import RiskAction
from app.repositories.base_repository import BaseRepository


class RiskActionRepository(BaseRepository[RiskAction]):
    pass


risk_action_repo = RiskActionRepository(RiskAction)
