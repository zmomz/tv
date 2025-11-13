from app.models.trading_models import Pyramid, DCAOrder, QueuedSignal
from app.repositories.base_repository import BaseRepository


class PyramidRepository(BaseRepository[Pyramid]):
    pass


class DCAOrderRepository(BaseRepository[DCAOrder]):
    pass


class QueuedSignalRepository(BaseRepository[QueuedSignal]):
    pass


pyramid_repo = PyramidRepository(Pyramid)
dca_order_repo = DCAOrderRepository(DCAOrder)
queued_signal_repo = QueuedSignalRepository(QueuedSignal)
