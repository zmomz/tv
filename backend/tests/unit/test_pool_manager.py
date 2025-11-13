import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from backend.app.services.pool_manager import ExecutionPoolManager
from backend.app.core.config import settings
from fastapi import Depends # Import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

@pytest.fixture
def mock_db_session():
    return MagicMock(spec=AsyncSession)

@pytest.mark.asyncio
async def test_pool_manager(mock_db_session):
    user_id = uuid4()
    pool_manager = ExecutionPoolManager(db=mock_db_session)

    # Mock the execute method for counting
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 0
    mock_db_session.execute.return_value = mock_result

    open_slots = await pool_manager.get_open_slots(user_id)
    can_open = await pool_manager.can_open_position(user_id)

    assert open_slots == settings.POOL_MAX_OPEN_GROUPS # Should return max_open_groups if no open positions
    assert can_open is True

    # Test when there are open positions
    mock_result.scalar_one.return_value = settings.POOL_MAX_OPEN_GROUPS # All slots filled
    open_slots = await pool_manager.get_open_slots(user_id)
    can_open = await pool_manager.can_open_position(user_id)

    assert open_slots == 0
    assert can_open is False