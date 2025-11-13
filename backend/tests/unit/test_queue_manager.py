import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4
from backend.app.services.queue_manager import QueueManager
from backend.app.models.trading_models import QueuedSignal
from backend.app.schemas.trading_schemas import SignalPayload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

@pytest.fixture
def mock_db_session():
    return MagicMock(spec=AsyncSession)

@pytest.fixture
def mock_signal_payload():
    return SignalPayload(
        secret="test",
        tv={'exchange': 'BINANCE', 'symbol': 'BTCUSDT', 'action': 'buy', 'timeframe': '1h'},
        execution_intent={'type': 'signal', 'side': 'buy'}
    )

@pytest.mark.asyncio
async def test_add_to_queue(mock_db_session, mock_signal_payload):
    user_id = uuid4()
    queue_manager = QueueManager(db=mock_db_session)

    # Mock the add, commit, and refresh methods
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = None
    mock_db_session.refresh.return_value = None

    queued_signal = await queue_manager.add_to_queue(mock_signal_payload, user_id)

    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(queued_signal)
    assert isinstance(queued_signal, QueuedSignal)
    assert queued_signal.user_id == user_id
    assert queued_signal.exchange == "BINANCE"
    assert queued_signal.symbol == "BTCUSDT"
    assert queued_signal.timeframe == "1h"
    assert queued_signal.status == "queued"
    assert queued_signal.replacement_count == 0
    assert queued_signal.priority_score == 0.0

@pytest.mark.asyncio
async def test_promote_next(mock_db_session, mock_signal_payload):
    user_id = uuid4()
    queue_manager = QueueManager(db=mock_db_session)

    # Setup mock for an existing queued signal
    mock_queued_signal = MagicMock(spec=QueuedSignal)
    mock_queued_signal.id = uuid4()
    mock_queued_signal.user_id = user_id
    mock_queued_signal.status = "queued"
    mock_queued_signal.queued_at = "2023-01-01T10:00:00"

    # Mock the execute method for async SQLAlchemy
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_queued_signal
    future_result = asyncio.Future()
    future_result.set_result(mock_result)
    mock_db_session.execute.return_value = future_result
    promoted_signal = await queue_manager.promote_next(user_id)

    assert promoted_signal is not None
    assert promoted_signal.id == mock_queued_signal.id
    assert promoted_signal.status == "processing"
    mock_db_session.add.assert_called_once_with(mock_queued_signal)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(promoted_signal)

@pytest.mark.asyncio
async def test_promote_next_no_signal(mock_db_session):
    user_id = uuid4()
    queue_manager = QueueManager(db=mock_db_session)

    # Mock the execute method for async SQLAlchemy to return None
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    future_result = asyncio.Future()
    future_result.set_result(mock_result)
    mock_db_session.execute.return_value = future_result
    promoted_signal = await queue_manager.promote_next(user_id)

    assert promoted_signal is None
    mock_db_session.commit.assert_not_called()
