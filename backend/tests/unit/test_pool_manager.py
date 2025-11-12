import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from backend.app.services.pool_manager import ExecutionPoolManager
from backend.app.core.config import settings

@pytest.fixture
def mock_db_session():
    return MagicMock()

def test_pool_manager(mock_db_session):
    user_id = uuid4()
    pool_manager = ExecutionPoolManager(db=mock_db_session)

    # Mock the query to return 0 live groups
    mock_db_session.query.return_value.filter.return_value.count.return_value = 0

    open_slots = pool_manager.get_open_slots(user_id)
    can_open = pool_manager.can_open_position(user_id)

    assert open_slots == 0
    assert can_open is False

            assert open_slots == 0    assert can_open is False
