from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.trading_models import PositionGroup, QueuedSignal
from uuid import UUID
from decimal import Decimal
from datetime import datetime

async def add_to_queue(db: AsyncSession, signal: dict, user_id: UUID) -> QueuedSignal:
    """
    Add a signal to the queue asynchronously.
    """
    priority_score = calculate_priority(signal)

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
    await db.commit()
    await db.refresh(queue_entry)
    return queue_entry

async def promote_from_queue(db: AsyncSession, user_id: UUID) -> QueuedSignal | None:
    """
    Promote a signal from the queue to a live position based on priority rules.
    """
    result = await db.execute(select(QueuedSignal).filter(QueuedSignal.user_id == user_id))
    queue_entries = result.scalars().all()

    if not queue_entries:
        return None

    sorted_entries = sorted(queue_entries,
                            key=lambda entry: (entry.priority_score, entry.replacement_count, entry.created_at),
                            reverse=True)

    highest_priority_entry = sorted_entries[0]

    highest_priority_entry.status = "promoted"
    await db.delete(highest_priority_entry)
    await db.commit()

    return highest_priority_entry

def calculate_priority(signal: dict) -> Decimal:
    """
    Calculate the priority of a signal in the queue.
    """
    return Decimal("0.0")

async def handle_signal_replacement(db: AsyncSession, new_signal: dict, user_id: UUID) -> None:
    """
    Handle a signal that is a replacement for an existing signal in the queue asynchronously.
    """
    result = await db.execute(select(QueuedSignal).filter(
        QueuedSignal.user_id == user_id,
        QueuedSignal.symbol == new_signal["symbol"]
    ))
    existing_entry = result.scalars().first()

    if existing_entry:
        existing_entry.original_signal = new_signal
        existing_entry.replacement_count += 1
        existing_entry.priority_score = calculate_priority(new_signal)
        await db.commit()
