from typing import Dict, Any, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import models
from ..db.session import get_async_db
from ..schemas.trading_schemas import SignalPayload # Import SignalPayload
from ..models.trading_models import QueuedSignal # Direct import of QueuedSignal

class QueueManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_to_queue(self, signal: SignalPayload, user_id: UUID) -> QueuedSignal:
        """Add signal to waiting queue"""
        new_queued_signal = QueuedSignal(
            user_id=user_id,
            exchange=signal.tv.get('exchange'), # Access attributes directly
            symbol=signal.tv.get('symbol'), # Access attributes directly
            timeframe=signal.tv.get('timeframe', '1m'), # Access attributes directly
            signal_payload=signal.model_dump_json(), # Store as JSON string
            status="queued", # Now 'status' is a valid column
            replacement_count=0,
            priority_score=0.0 # Renamed from priority_rank
        )
        self.db.add(new_queued_signal)
        await self.db.commit()
        await self.db.refresh(new_queued_signal)
        return new_queued_signal

    async def replace_signal(self, existing_id: UUID, new_signal: SignalPayload) -> Optional[QueuedSignal]:
        """Replace queued signal, increment counter"""
        # TODO: Implement replacement logic
        return None

    async def calculate_priority(self, signal: SignalPayload) -> float:
        """Score signal based on priority rules"""
        # TODO: Implement priority algorithm
        return 0.0

    async def promote_next(self, user_id: UUID) -> Optional[QueuedSignal]:
        """Get highest priority queued signal"""
        # For now, just return the oldest queued signal
        result = await self.db.execute(
            select(QueuedSignal).filter(
                QueuedSignal.user_id == user_id,
                QueuedSignal.status == "queued"
            ).order_by(QueuedSignal.queued_at)
        )
        promoted_signal = (await result).scalars().first()

        if promoted_signal:
            promoted_signal.status = "processing"
            self.db.add(promoted_signal)
            await self.db.commit()
            await self.db.refresh(promoted_signal)
        return promoted_signal

def get_queue_manager(db: AsyncSession = Depends(get_async_db)) -> QueueManager:
    return QueueManager(db)
