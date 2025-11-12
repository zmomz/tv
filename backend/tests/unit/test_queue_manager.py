import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from backend.app.services.queue_manager import QueueManager
from backend.app.models.trading_models import QueueEntry
from backend.app.schemas.trading_schemas import SignalPayload

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def mock_signal_payload():
    return SignalPayload(
        secret="test",
        tv={'exchange': 'BINANCE', 'symbol': 'BTCUSDT', 'action': 'buy', 'timeframe': '1h'},
        execution_intent={'type': 'signal', 'side': 'buy'}
    )

def test_add_to_queue(mock_db_session, mock_signal_payload):
    user_id = uuid4()
    queue_manager = QueueManager(db=mock_db_session)

    # Mock the add and commit methods
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = None
    mock_db_session.refresh.return_value = None

    queued_signal = queue_manager.add_to_queue(mock_signal_payload, user_id)

    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(queued_signal)
    assert isinstance(queued_signal, QueueEntry)
    assert queued_signal.user_id == user_id
    assert queued_signal.exchange == "BINANCE"
    assert queued_signal.symbol == "BTCUSDT"
    assert queued_signal.timeframe == "1h"
    assert queued_signal.status == "queued"
    assert queued_signal.replacement_count == 0
    assert queued_signal.priority_score == 0.0

def test_promote_next(mock_db_session, mock_signal_payload):
    user_id = uuid4()
    queue_manager = QueueManager(db=mock_db_session)

    # Setup mock for an existing queued signal
    mock_queued_signal = MagicMock(spec=QueueEntry)
    mock_queued_signal.id = uuid4()
    mock_queued_signal.user_id = user_id
    mock_queued_signal.status = "queued"
    mock_queued_signal.created_at = "2023-01-01T10:00:00"

    mock_db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_queued_signal

    promoted_signal = queue_manager.promote_next(user_id)

    assert promoted_signal is not None
    assert promoted_signal.id == mock_queued_signal.id
    assert promoted_signal.status == "processing"
    mock_db_session.commit.assert_called_once()

def test_promote_next_no_signal(mock_db_session):
    user_id = uuid4()
    queue_manager = QueueManager(db=mock_db_session)

    mock_db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    promoted_signal = queue_manager.promote_next(user_id)

    assert promoted_signal is None
    mock_db_session.commit.assert_not_called()
