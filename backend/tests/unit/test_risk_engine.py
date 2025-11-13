import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timedelta
from backend.app.services.risk_engine import RiskEngine
from backend.app.models.trading_models import PositionGroup, Pyramid, PositionGroupStatus
from backend.app.models.risk_analytics_models import RiskAction
from backend.app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

@pytest.fixture
def mock_db_session():
    return MagicMock(spec=AsyncSession)

@pytest.fixture
def risk_engine(mock_db_session):
    return RiskEngine(db=mock_db_session)

@pytest.fixture
def mock_position_group():
    pg = MagicMock(spec=PositionGroup)
    pg.id = uuid4()
    pg.user_id = uuid4()
    pg.exchange_config_id = uuid4()
    pg.exchange = "binance"
    pg.symbol = "BTCUSDT"
    pg.timeframe = 15
    pg.side = "long"
    pg.status = PositionGroupStatus.LIVE # Use Enum member
    pg.unrealized_pnl_percent = Decimal("-5.0")
    pg.unrealized_pnl_usd = Decimal("-100.0")
    pg.created_at = datetime.utcnow()
    return pg

@pytest.mark.asyncio
async def test_should_activate_risk_engine(risk_engine, mock_position_group):
    # Mock pyramid count
    mock_count_result = MagicMock()
    mock_count_result.scalar_one.return_value = 5
    
    mock_last_pyramid = MagicMock(spec=Pyramid)
    mock_last_pyramid.entry_timestamp = datetime.utcnow() - timedelta(minutes=settings.RISK_POST_FULL_WAIT_MINUTES + 1)
    mock_pyramid_result = MagicMock()
    mock_pyramid_result.scalars.return_value.first.return_value = mock_last_pyramid
    
    future_count_result = asyncio.Future()
    future_count_result.set_result(mock_count_result)
    future_pyramid_result = asyncio.Future()
    future_pyramid_result.set_result(mock_pyramid_result)
    risk_engine.db.execute.side_effect = [future_count_result, future_pyramid_result, future_count_result, future_pyramid_result] # For multiple execute calls
    # Test case 1: PnL % is below threshold, should activate
    mock_position_group.unrealized_pnl_percent = Decimal(str(settings.RISK_LOSS_THRESHOLD_PERCENT)) - Decimal("1.0")
    assert await risk_engine.should_activate_risk_engine(mock_position_group, mock_position_group.unrealized_pnl_percent) is True

    # Test case 2: PnL % is above threshold, should not activate
    mock_position_group.unrealized_pnl_percent = Decimal(str(settings.RISK_LOSS_THRESHOLD_PERCENT)) + Decimal("1.0")
    assert await risk_engine.should_activate_risk_engine(mock_position_group, mock_position_group.unrealized_pnl_percent) is False

@pytest.mark.asyncio
async def test_find_losing_positions(risk_engine, mock_db_session):
    user_id = uuid4()

    losing_group_1 = MagicMock(spec=PositionGroup, id=uuid4(), unrealized_pnl_percent=Decimal("-10.0"), unrealized_pnl_usd=Decimal("-100.0"), created_at=datetime.utcnow() - timedelta(minutes=10))
    losing_group_2 = MagicMock(spec=PositionGroup, id=uuid4(), unrealized_pnl_percent=Decimal("-12.0"), unrealized_pnl_usd=Decimal("-150.0"), created_at=datetime.utcnow() - timedelta(minutes=5))
    losing_group_3 = MagicMock(spec=PositionGroup, id=uuid4(), unrealized_pnl_percent=Decimal("-8.0"), unrealized_pnl_usd=Decimal("-80.0"), created_at=datetime.utcnow() - timedelta(minutes=15))

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        losing_group_1, losing_group_2, losing_group_3
    ]
    future_result = asyncio.Future()
    future_result.set_result(mock_result)
    mock_db_session.execute.return_value = future_result
    selected_groups = await risk_engine.find_losing_positions(user_id)
    assert selected_groups[0].id == losing_group_2.id # Should select the one with worst PnL %

@pytest.mark.asyncio
async def test_find_winning_positions(risk_engine, mock_db_session):
    user_id = uuid4()

    winning_group_1 = MagicMock(spec=PositionGroup, id=uuid4(), unrealized_pnl_usd=Decimal("200.0"), created_at=datetime.utcnow() - timedelta(minutes=10))
    winning_group_2 = MagicMock(spec=PositionGroup, id=uuid4(), unrealized_pnl_usd=Decimal("150.0"), created_at=datetime.utcnow() - timedelta(minutes=5))
    winning_group_3 = MagicMock(spec=PositionGroup, id=uuid4(), unrealized_pnl_usd=Decimal("300.0"), created_at=datetime.utcnow() - timedelta(minutes=15))

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        winning_group_1, winning_group_2, winning_group_3
    ]
    future_result = asyncio.Future()
    future_result.set_result(mock_result)
    mock_db_session.execute.return_value = future_result
    selected_groups = await risk_engine.find_winning_positions(user_id)
    assert selected_groups[0].id == winning_group_3.id # Should select the one with highest PnL USD

@pytest.mark.asyncio
async def test_execute_risk_mitigation(risk_engine, mock_db_session, mock_position_group):
    losing_group = mock_position_group
    losing_group.unrealized_pnl_usd = Decimal("-300.0")

    winning_group_1 = MagicMock(spec=PositionGroup, id=uuid4(), unrealized_pnl_usd=Decimal("100.0"))
    winning_group_2 = MagicMock(spec=PositionGroup, id=uuid4(), unrealized_pnl_usd=Decimal("200.0"))

    winning_positions = [winning_group_1, winning_group_2]

    with patch('backend.app.services.risk_engine.place_partial_close_order', new_callable=AsyncMock) as mock_place_order:
        await risk_engine.execute_risk_mitigation(losing_group, winning_positions)

        mock_place_order.assert_any_call(db=mock_db_session, position_group=winning_group_1, usd_amount_to_realize=Decimal("100.0"))
        mock_place_order.assert_any_call(db=mock_db_session, position_group=winning_group_2, usd_amount_to_realize=Decimal("200.0"))
        mock_db_session.add.assert_called_once()
        await mock_db_session.commit()
        mock_db_session.commit.assert_called_once()