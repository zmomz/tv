import pytest
from unittest.mock import MagicMock, patch, ANY
from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal

from backend.app.services.pool_manager import ExecutionPoolManager
from backend.app.models.trading_models import PositionGroup
from backend.app.core.config import settings

@pytest.fixture
def mock_db_session():
    """Mocks a SQLAlchemy database session."""
    return MagicMock(spec=Session)

@pytest.fixture
def mock_position_group():
    """
    Mocks a PositionGroup instance.
    Note: user_id is a UUID in the actual models.
    """
    pg = MagicMock(spec=PositionGroup)
    pg.id = UUID('12345678-1234-5678-1234-567812345678')
    pg.user_id = UUID('00000000-0000-0000-0000-000000000001')
    pg.exchange = "binance"
    pg.symbol = "BTC/USDT"
    pg.status = "live"
    return pg

@pytest.mark.parametrize("max_groups, live_groups, expected_slots", [
    (5, 2, 3),
    (5, 5, 0),
    (5, 0, 5),
    (5, 6, -1), # Over-capacity scenario
])
def test_get_open_slots(mock_db_session, mock_position_group, max_groups, live_groups, expected_slots):
    """
    Test that get_open_slots correctly calculates the number of available slots.
    """
    # Mock settings.POOL_MAX_OPEN_GROUPS
    with patch.object(settings, 'POOL_MAX_OPEN_GROUPS', max_groups):
        # Mock the database query count
        mock_db_session.query.return_value.filter.return_value.count.return_value = live_groups

        manager = ExecutionPoolManager(mock_db_session)
        user_id = mock_position_group.user_id # Use UUID for user_id
        slots = manager.get_open_slots(user_id)

        assert slots == expected_slots
        mock_db_session.query.assert_called_once_with(PositionGroup)
        mock_db_session.query.return_value.filter.assert_called_once_with(ANY, ANY)

@pytest.mark.parametrize("max_groups, live_groups, expected_can_open", [
    (5, 2, True),
    (5, 5, False),
    (5, 0, True),
    (5, 6, False), # Over-capacity scenario
])
def test_can_open_position(mock_db_session, mock_position_group, max_groups, live_groups, expected_can_open):
    """
    Test that can_open_position correctly determines if a new position can be opened.
    """
    with patch.object(settings, 'POOL_MAX_OPEN_GROUPS', max_groups):
        mock_db_session.query.return_value.filter.return_value.count.return_value = live_groups

        manager = ExecutionPoolManager(mock_db_session)
        user_id = mock_position_group.user_id # Use UUID for user_id
        can_open = manager.can_open_position(user_id)

        assert can_open == expected_can_open
        mock_db_session.query.assert_called_once_with(PositionGroup)
        mock_db_session.query.return_value.filter.assert_called_once_with(ANY, ANY)
