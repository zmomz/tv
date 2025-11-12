from typing import Dict, Any, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.orm import Session
from ..models import models
from ..db.session import get_db
from ..schemas.trading_schemas import SignalPayload # Import SignalPayload
from ..models.trading_models import QueueEntry # Direct import of QueueEntry

class QueueManager:
    def __init__(self, db: Session):
        self.db = db

    def add_to_queue(self, signal: SignalPayload, user_id: UUID) -> QueueEntry:
        """Add signal to waiting queue"""
        new_queued_signal = QueueEntry(
            user_id=user_id,
            exchange=signal.tv.get('exchange'), # Access attributes directly
            symbol=signal.tv.get('symbol'), # Access attributes directly
            timeframe=signal.tv.get('timeframe', '1m'), # Access attributes directly
            original_signal=signal.model_dump_json(), # Store as JSON string
            status="queued", # Now 'status' is a valid column
            replacement_count=0,
            priority_score=0.0 # Renamed from priority_rank
        )
        self.db.add(new_queued_signal)
        self.db.commit()
        self.db.refresh(new_queued_signal)
        return new_queued_signal

    def replace_signal(self, existing_id: UUID, new_signal: SignalPayload) -> Optional[QueueEntry]:
        """Replace queued signal, increment counter"""
        # TODO: Implement replacement logic
        return None

    def calculate_priority(self, signal: SignalPayload) -> float:
        """Score signal based on priority rules"""
        # TODO: Implement priority algorithm
        return 0.0

    def promote_next(self, user_id: UUID) -> Optional[QueueEntry]:
        """Get highest priority queued signal"""
        # For now, just return the oldest queued signal
        promoted_signal = self.db.query(QueueEntry).filter(
            QueueEntry.user_id == user_id,
            QueueEntry.status == "queued"
        ).order_by(QueueEntry.created_at).first()

        if promoted_signal:
            promoted_signal.status = "processing"
            self.db.commit()
            self.db.refresh(promoted_signal)
        return promoted_signal

def get_queue_manager(db: Session = Depends(get_db)) -> QueueManager:
    return QueueManager(db)
