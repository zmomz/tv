import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.tp_manager import TPManager
from backend.app.models.trading_models import PositionGroup, Pyramid
from backend.app.core.config import settings

@pytest.fixture
def mock_db_session():
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    return session

@pytest.fixture
def tp_manager(mock_db_session):
    return TPManager(db=mock_db_session)

@pytest.fixture
def mock_position_group():
    pg = MagicMock(spec=PositionGroup)
    pg.id = uuid4()
    pg.user_id = uuid4()
    pg.api_key_id = uuid4()
    pg.pair = "BTCUSDT"
    pg.timeframe = "1h"
    pg.status = "Live"
    pg.current_price = Decimal("30000")
    pg.pyramids = []
    return pg

@pytest.fixture
def mock_pyramid():
    pyr = MagicMock(spec=Pyramid)
    pyr.id = uuid4()
    pyr.entry_price = Decimal("29000")
    pyr.take_profit_price = Decimal("30000")
    pyr.status = "open"
    return pyr

@pytest.mark.asyncio
async def test_check_per_leg_tp_hit(tp_manager, mock_position_group, mock_pyramid, mock_db_session):
    mock_position_group.pyramids = [mock_pyramid]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_pyramid]
    future_result = asyncio.Future()
    future_result.set_result(mock_result)
    mock_db_session.execute.return_value = future_result

    tp_hit_result = await tp_manager.check_per_leg_tp(mock_position_group)

    assert tp_hit_result is not None
    assert tp_hit_result['group_id'] == mock_position_group.id
    assert tp_hit_result['pyramid_id'] == mock_pyramid.id
    assert tp_hit_result['take_profit_price'] == mock_pyramid.take_profit_price
    assert mock_pyramid.status == "closed"
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_check_per_leg_tp_not_hit(tp_manager, mock_position_group, mock_pyramid, mock_db_session):
    mock_position_group.pyramids = [mock_pyramid]
    mock_position_group.current_price = Decimal("29500") # Price does not hit TP

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_pyramid]
    future_result = asyncio.Future()
    future_result.set_result(mock_result)
    mock_db_session.execute.return_value = future_result

    tp_hit_result = await tp_manager.check_per_leg_tp(mock_position_group)

    assert tp_hit_result is None
    assert mock_pyramid.status == "open"
    mock_db_session.commit.assert_not_called()

@pytest.mark.asyncio
async def test_check_per_leg_tp_no_open_pyramids(tp_manager, mock_position_group, mock_db_session):
    mock_position_group.pyramids = []
    mock_position_group.current_price = Decimal("30000")

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    future_result = asyncio.Future()
    future_result.set_result(mock_result)
    mock_db_session.execute.return_value = future_result

    tp_hit_result = await tp_manager.check_per_leg_tp(mock_position_group)

    assert tp_hit_result is None
    mock_db_session.commit.assert_not_called()
