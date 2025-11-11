import pytest
from unittest.mock import MagicMock, patch, ANY
from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal
from datetime import datetime # Import datetime

from backend.app.services.queue_service import add_to_queue, handle_signal_replacement, promote_from_queue, calculate_priority
from backend.app.models.trading_models import QueueEntry, PositionGroup # Import PositionGroup for potential future use

@pytest.fixture
def mock_db_session():
    """Mocks a SQLAlchemy database session."""
    return MagicMock(spec=Session)

@pytest.fixture
def mock_user_id():
    return UUID('00000000-0000-0000-0000-000000000001')

@pytest.fixture
def mock_signal():
    return {
        "symbol": "BTC/USDT",
        "exchange": "binance",
        "timeframe": "1h",
        "execution_intent": {"action": "buy", "amount": 0.001, "strategy": "grid"}
    }

def test_add_to_queue_creates_new_entry(mock_db_session, mock_signal, mock_user_id):
    """
    Test that add_to_queue creates and persists a new QueueEntry.
    """
    # Mock the QueueEntry constructor to return a MagicMock instance
    with patch('backend.app.services.queue_service.QueueEntry') as MockQueueEntry:
        mock_queue_entry_instance = MockQueueEntry.return_value
        mock_queue_entry_instance.priority_score = Decimal("0.0") # Default value
        mock_queue_entry_instance.replacement_count = 0 # Default value

        # Mock calculate_priority to return a specific value
        with patch('backend.app.services.queue_service.calculate_priority', return_value=Decimal("100.0")) as mock_calc_priority:
            queue_entry = add_to_queue(mock_db_session, mock_signal, mock_user_id)

            # Assertions
            MockQueueEntry.assert_called_once_with(
                user_id=mock_user_id,
                exchange=mock_signal["exchange"],
                symbol=mock_signal["symbol"],
                timeframe=mock_signal["timeframe"],
                original_signal=mock_signal,
                priority_score=Decimal("100.0"),
                replacement_count=0
            )
            mock_db_session.add.assert_called_once_with(mock_queue_entry_instance)
            mock_db_session.commit.assert_called_once()
            assert queue_entry == mock_queue_entry_instance

def test_handle_signal_replacement_updates_existing_entry(mock_db_session, mock_signal, mock_user_id):
    """
    Test that handle_signal_replacement updates an existing QueueEntry and increments replacement_count.
    """
    existing_entry = MagicMock(spec=QueueEntry)
    existing_entry.original_signal = {"old_data": True}
    existing_entry.replacement_count = 5
    existing_entry.priority_score = Decimal("50.0")

    mock_db_session.query.return_value.filter.return_value.first.return_value = existing_entry

    with patch('backend.app.services.queue_service.calculate_priority', return_value=Decimal("150.0")) as mock_calc_priority:
        handle_signal_replacement(mock_db_session, mock_signal, mock_user_id)

        # Assertions
        mock_db_session.query.assert_called_once_with(QueueEntry)
        mock_db_session.query.return_value.filter.assert_called_once_with(ANY, ANY)
        assert existing_entry.original_signal == mock_signal
        assert existing_entry.replacement_count == 6
        assert existing_entry.priority_score == Decimal("150.0")
        mock_db_session.commit.assert_called_once()

def test_handle_signal_replacement_no_existing_entry(mock_db_session, mock_signal, mock_user_id):
    """
    Test that handle_signal_replacement does nothing if no existing entry is found.
    """
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    handle_signal_replacement(mock_db_session, mock_signal, mock_user_id)

    # Assertions
    mock_db_session.query.assert_called_once_with(QueueEntry)
    mock_db_session.query.return_value.filter.assert_called_once_with(ANY, ANY)
    mock_db_session.commit.assert_not_called()

@pytest.mark.asyncio
async def test_promote_from_queue_selects_highest_priority(mock_db_session, mock_user_id):
    """
    Test that promote_from_queue selects the highest priority signal based on SoW rules.
    Priority rules: 1) Pyramid continuation, 2) Deepest loss, 3) Highest replacement, 4) FIFO.
    For this test, we'll focus on replacement count and FIFO for simplicity.
    """
    # Setup: Multiple queue entries with different priorities
    entry_low_priority = MagicMock(spec=QueueEntry)
    entry_low_priority.id = UUID('11111111-1111-1111-1111-111111111111')
    entry_low_priority.priority_score = Decimal("10.0")
    entry_low_priority.replacement_count = 0
    entry_low_priority.created_at = datetime(2023, 1, 1, 10, 0, 0)
    entry_low_priority.original_signal = {"symbol": "LOW/USDT"}

    entry_high_replacement = MagicMock(spec=QueueEntry)
    entry_high_replacement.id = UUID('22222222-2222-2222-2222-222222222222')
    entry_high_replacement.priority_score = Decimal("20.0")
    entry_high_replacement.replacement_count = 5
    entry_high_replacement.created_at = datetime(2023, 1, 1, 11, 0, 0)
    entry_high_replacement.original_signal = {"symbol": "HIGH_REP/USDT"}

    entry_fifo = MagicMock(spec=QueueEntry)
    entry_fifo.id = UUID('33333333-3333-3333-3333-333333333333')
    entry_fifo.priority_score = Decimal("20.0")
    entry_fifo.replacement_count = 0
    entry_fifo.created_at = datetime(2023, 1, 1, 9, 0, 0) # Older than high_replacement
    entry_fifo.original_signal = {"symbol": "FIFO/USDT"}

    # Mock the database query to return these entries
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        entry_low_priority, entry_high_replacement, entry_fifo
    ]

    # Mock the calculate_priority function to return consistent values for testing sorting
    with patch('backend.app.services.queue_service.calculate_priority', side_effect=lambda signal: {
        "LOW/USDT": Decimal("10.0"),
        "HIGH_REP/USDT": Decimal("20.0"),
        "FIFO/USDT": Decimal("20.0"),
    }.get(signal["symbol"], Decimal("0.0"))) as mock_calc_priority:

        promoted_entry = await promote_from_queue(mock_db_session, mock_user_id)

        # Assertions
        mock_db_session.query.assert_called_once_with(QueueEntry)
        mock_db_session.query.return_value.filter.assert_called_once_with(ANY)
        # The application code sorts in Python, so no order_by assertion here.
        
        # The expected order based on on SoW rules (priority_score then replacement_count then created_at)
        # Given the mock priority scores, entry_high_replacement and entry_fifo have the same priority.
        # Then, entry_high_replacement has higher replacement_count (5 vs 0).
        # So, entry_high_replacement should be promoted.
        assert promoted_entry == entry_high_replacement
        assert promoted_entry.status == "promoted" # Assuming a 'promoted' status
        mock_db_session.delete.assert_called_once_with(entry_high_replacement)
        mock_db_session.commit.assert_called_once()
@pytest.mark.asyncio
async def test_promote_from_queue_returns_none_if_empty(mock_db_session, mock_user_id):
    """
    Test that promote_from_queue returns None if the queue is empty.
    """
    mock_db_session.query.return_value.filter.return_value.all.return_value = []

    promoted_entry = await promote_from_queue(mock_db_session, mock_user_id)

    assert promoted_entry is None
    mock_db_session.query.assert_called_once_with(QueueEntry)
    mock_db_session.query.return_value.filter.assert_called_once_with(ANY)
    mock_db_session.delete.assert_not_called()
    mock_db_session.commit.assert_not_called()
