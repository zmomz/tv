from sqlalchemy.orm import Session
from ..models.trading_models import PositionGroup, QueuedSignal # Import QueuedSignal
from uuid import UUID
from decimal import Decimal
from datetime import datetime # Import datetime

def add_to_queue(db: Session, signal: dict, user_id: UUID) -> QueuedSignal:
    """
    Add a signal to the queue.
    """
    priority_score = calculate_priority(signal) # calculate_priority will be updated later to take signal directly

    queue_entry = QueuedSignal(
        user_id=user_id,
        exchange=signal["exchange"],
        symbol=signal["symbol"],
        timeframe=signal["timeframe"],
        original_signal=signal,
        priority_score=priority_score,
        replacement_count=0
    )
    db.add(queue_entry)
    db.commit()
    return queue_entry

async def promote_from_queue(db: Session, user_id: UUID) -> QueuedSignal | None:
    """
    Promote a signal from the queue to a live position based on priority rules.
    Priority rules: 1) Highest priority_score, 2) Highest replacement_count, 3) FIFO (oldest created_at).
    """
    # Query for all queue entries for the user
    queue_entries = db.query(QueuedSignal).filter(
        QueuedSignal.user_id == user_id
    ).all()

    if not queue_entries:
        return None

    # Sort by priority rules: priority_score (desc), replacement_count (desc), created_at (asc)
    # Python's sort is stable, so we can sort by multiple keys in reverse order of importance
    sorted_entries = sorted(queue_entries,
                            key=lambda entry: (entry.priority_score, entry.replacement_count, entry.created_at),
                            reverse=True)

    highest_priority_entry = sorted_entries[0]

    # Mark as promoted and delete from queue
    highest_priority_entry.status = "promoted" # Assuming QueuedSignal has a status field
    db.delete(highest_priority_entry)
    db.commit()

    return highest_priority_entry

def calculate_priority(signal: dict) -> Decimal:
    """
    Calculate the priority of a signal in the queue.
    """
    # This is a placeholder. In a real-world application, you would
    # implement the logic to calculate the priority of a signal.
    return Decimal("0.0")

def handle_signal_replacement(db: Session, new_signal: dict, user_id: UUID) -> None:
    """
    Handle a signal that is a replacement for an existing signal in
    the queue.
    """
    existing_entry = db.query(QueuedSignal).filter(
        QueuedSignal.user_id == user_id,
        QueuedSignal.symbol == new_signal["symbol"]
    ).first()

    if existing_entry:
        existing_entry.original_signal = new_signal
        existing_entry.replacement_count += 1
        existing_entry.priority_score = calculate_priority(new_signal) # Recalculate priority
        db.commit()