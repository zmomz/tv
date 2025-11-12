import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timedelta
from backend.app.services.risk_engine import RiskEngine
from backend.app.models.trading_models import PositionGroup, Pyramid
from backend.app.core.config import settings

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def risk_engine(mock_db_session):
    return RiskEngine(db=mock_db_session)

@pytest.fixture
def mock_position_group():
    pg = MagicMock(spec=PositionGroup)
    pg.id = uuid4()
    pg.user_id = uuid4()
    pg.api_key_id = uuid4()
    pg.pair = "BTCUSDT"
    pg.timeframe = "1h"
    pg.status = "Live"
    pg.unrealized_pnl_percent = Decimal("-5.0")
    pg.unrealized_pnl_usd = Decimal("-100.0")
    pg.created_at = datetime.utcnow()
    return pg

@pytest.mark.asyncio
async def test_should_activate_risk_engine(risk_engine, mock_position_group):
    # Mock pyramid count and last_pyramid.created_at
    risk_engine.db.query.return_value.filter.return_value.count.return_value = 5
    mock_last_pyramid = MagicMock(spec=Pyramid)
    mock_last_pyramid.created_at = datetime.utcnow() - timedelta(minutes=settings.RISK_POST_FULL_WAIT_MINUTES + 1)
    risk_engine.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_last_pyramid

    # Test case 1: PnL % is below threshold, should activate
    mock_position_group.unrealized_pnl_percent = Decimal(str(settings.RISK_LOSS_THRESHOLD_PERCENT)) - Decimal("1.0")
    assert risk_engine.should_activate_risk_engine(mock_position_group, mock_position_group.unrealized_pnl_percent) is True

    # Test case 2: PnL % is above threshold, should not activate
    mock_position_group.unrealized_pnl_percent = Decimal(str(settings.RISK_LOSS_THRESHOLD_PERCENT)) + Decimal("1.0")
    assert risk_engine.should_activate_risk_engine(mock_position_group, mock_position_group.unrealized_pnl_percent) is False

@pytest.mark.asyncio
async def test_find_losing_positions(risk_engine, mock_db_session):
    user_id = uuid4()

    losing_group_1 = MagicMock(spec=PositionGroup, id=uuid4(), unrealized_pnl_percent=Decimal("-10.0"), unrealized_pnl_usd=Decimal("-100.0"), created_at=datetime.utcnow() - timedelta(minutes=10))
    losing_group_2 = MagicMock(spec=PositionGroup, id=uuid4(), unrealized_pnl_percent=Decimal("-12.0"), unrealized_pnl_usd=Decimal("-150.0"), created_at=datetime.utcnow() - timedelta(minutes=5))
    losing_group_3 = MagicMock(spec=PositionGroup, id=uuid4(), unrealized_pnl_percent=Decimal("-8.0"), unrealized_pnl_usd=Decimal("-80.0"), created_at=datetime.utcnow() - timedelta(minutes=15))

    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        losing_group_1, losing_group_2, losing_group_3
    ]

    selected_groups = await risk_engine.find_losing_positions(user_id)
    assert selected_groups[0].id == losing_group_2.id # Should select the one with worst PnL %

@pytest.mark.asyncio
async def test_find_winning_positions(risk_engine, mock_db_session):
    user_id = uuid4()

    winning_group_1 = MagicMock(spec=PositionGroup, id=uuid4(), unrealized_pnl_usd=Decimal("200.0"), created_at=datetime.utcnow() - timedelta(minutes=10))
    winning_group_2 = MagicMock(spec=PositionGroup, id=uuid4(), unrealized_pnl_usd=Decimal("150.0"), created_at=datetime.utcnow() - timedelta(minutes=5))
    winning_group_3 = MagicMock(spec=PositionGroup, id=uuid4(), unrealized_pnl_usd=Decimal("300.0"), created_at=datetime.utcnow() - timedelta(minutes=15))

    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        winning_group_1, winning_group_2, winning_group_3
    ]

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
        mock_db_session.commit.assert_called_once()
