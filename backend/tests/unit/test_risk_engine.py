import pytest
from unittest.mock import MagicMock, patch, ANY
from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timedelta

from backend.app.services.risk_engine import RiskEngine
from backend.app.models.trading_models import PositionGroup, Pyramid
from backend.app.core.config import settings

@pytest.fixture
def mock_db_session():
    """Mocks a SQLAlchemy database session."""
    return MagicMock(spec=Session)

@pytest.fixture
def mock_user_id():
    return UUID('00000000-0000-0000-0000-000000000001')

@pytest.fixture
def mock_position_group():
    """Mocks a PositionGroup instance."""
    pg = MagicMock(spec=PositionGroup)
    pg.id = UUID('12345678-1234-5678-1234-567812345678')
    pg.user_id = UUID('00000000-0000-0000-0000-000000000001')
    pg.created_at = datetime.utcnow()
    return pg

def test_should_activate_risk_engine_all_conditions_met(mock_db_session, mock_position_group):
    """
    Test that should_activate_risk_engine returns True when all activation conditions are met.
    """
    # Mock pyramid count to be 5 (full)
    mock_db_session.query.return_value.filter.return_value.count.return_value = 5
    
    # Mock unrealized PnL to be below the activation threshold
    unrealized_pnl_percent = Decimal("-6.0")

    # Mock the last pyramid entry time to be older than the wait time
    last_pyramid_entry_time = datetime.utcnow() - timedelta(seconds=4000)
    mock_pyramid = MagicMock(spec=Pyramid)
    mock_pyramid.created_at = last_pyramid_entry_time
    mock_db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_pyramid

    with (
        patch.object(settings, 'RISK_LOSS_THRESHOLD_PERCENT', Decimal("-5.0")),
        patch.object(settings, 'RISK_REQUIRE_FULL_PYRAMIDS', True),
        patch.object(settings, 'RISK_POST_FULL_WAIT_MINUTES', 60),
    ):
        engine = RiskEngine(mock_db_session)
        should_activate = engine.should_activate_risk_engine(mock_position_group, unrealized_pnl_percent)

        assert should_activate is True

def test_should_activate_risk_engine_pyramid_not_full(mock_db_session, mock_position_group):
    """
    Test that should_activate_risk_engine returns False if the pyramid is not full.
    """
    # Mock pyramid count to be less than 5
    mock_db_session.query.return_value.filter.return_value.count.return_value = 4
    unrealized_pnl_percent = Decimal("-6.0")

    with (
        patch.object(settings, 'RISK_LOSS_THRESHOLD_PERCENT', Decimal("-5.0")),
        patch.object(settings, 'RISK_REQUIRE_FULL_PYRAMIDS', True),
        patch.object(settings, 'RISK_POST_FULL_WAIT_MINUTES', 60),
    ):
        engine = RiskEngine(mock_db_session)
        should_activate = engine.should_activate_risk_engine(mock_position_group, unrealized_pnl_percent)

        assert should_activate is False

def test_should_activate_risk_engine_pnl_above_threshold(mock_db_session, mock_position_group):
    """
    Test that should_activate_risk_engine returns False if the PnL is above the threshold.
    """
    mock_db_session.query.return_value.filter.return_value.count.return_value = 5
    # Mock unrealized PnL to be above the activation threshold
    unrealized_pnl_percent = Decimal("-4.0")

    with (
        patch.object(settings, 'RISK_LOSS_THRESHOLD_PERCENT', Decimal("-5.0")),
        patch.object(settings, 'RISK_REQUIRE_FULL_PYRAMIDS', True),
        patch.object(settings, 'RISK_POST_FULL_WAIT_MINUTES', 60),
    ):
        engine = RiskEngine(mock_db_session)
        should_activate = engine.should_activate_risk_engine(mock_position_group, unrealized_pnl_percent)

        assert should_activate is False

def test_should_activate_risk_engine_wait_time_not_passed(mock_db_session, mock_position_group):
    """
    Test that should_activate_risk_engine returns False if the post-full-pyramid wait time has not passed.
    """
    mock_db_session.query.return_value.filter.return_value.count.return_value = 5
    unrealized_pnl_percent = Decimal("-6.0")
    # Mock the last pyramid entry time to be more recent than the wait time
    last_pyramid_entry_time = datetime.utcnow() - timedelta(seconds=3000)
    mock_pyramid = MagicMock(spec=Pyramid)
    mock_pyramid.created_at = last_pyramid_entry_time
    mock_db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_pyramid

    with (
        patch.object(settings, 'RISK_LOSS_THRESHOLD_PERCENT', Decimal("-5.0")),
        patch.object(settings, 'RISK_REQUIRE_FULL_PYRAMIDS', True),
        patch.object(settings, 'RISK_POST_FULL_WAIT_MINUTES', 60),
    ):
        engine = RiskEngine(mock_db_session)
        should_activate = engine.should_activate_risk_engine(mock_position_group, unrealized_pnl_percent)

        assert should_activate is False

@pytest.mark.asyncio
async def test_find_and_rank_losing_positions(mock_db_session, mock_user_id):
    """
    Test that find_and_rank_losing_positions correctly identifies and ranks losing positions.
    Ranking rules: 1) highest loss percent, 2) highest unrealized dollar loss, 3) oldest trade.
    """
    # Mock PositionGroup instances
    pg1 = MagicMock(spec=PositionGroup)
    pg1.id = UUID('11111111-1111-1111-1111-111111111111')
    pg1.created_at = datetime.utcnow() - timedelta(days=10) # Oldest
    pg1.unrealized_pnl_percent = Decimal("-10.0") # Highest loss percent
    pg1.unrealized_pnl_usd = Decimal("-1000.0") # Highest USD loss

    pg2 = MagicMock(spec=PositionGroup)
    pg2.id = UUID('22222222-2222-2222-2222-222222222222')
    pg2.created_at = datetime.utcnow() - timedelta(days=5)
    pg2.unrealized_pnl_percent = Decimal("-8.0")
    pg2.unrealized_pnl_usd = Decimal("-1200.0") # Higher USD loss than pg1, but lower percent

    pg3 = MagicMock(spec=PositionGroup)
    pg3.id = UUID('33333333-3333-3333-3333-333333333333')
    pg3.created_at = datetime.utcnow() - timedelta(days=15) # Even older, but lower loss
    pg3.unrealized_pnl_percent = Decimal("-5.0")
    pg3.unrealized_pnl_usd = Decimal("-500.0")

    # Mock the database query to return only the losing position groups after filtering
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        pg1, pg2, pg3
    ]
    engine = RiskEngine(mock_db_session)
    losing_positions = await engine.find_losing_positions(mock_user_id)

    # Assertions
    mock_db_session.query.assert_called_once_with(PositionGroup)
    mock_db_session.query.return_value.filter.assert_called_once_with(ANY, ANY, ANY) # Filter by user_id, status, and pnl_percent

    # Expected order: pg1 (highest percent loss), pg2 (next highest percent loss), pg3 (lowest percent loss)
    assert len(losing_positions) == 3
    assert losing_positions[0] == pg1
    assert losing_positions[1] == pg2
    assert losing_positions[2] == pg3

@pytest.mark.asyncio
async def test_find_and_rank_winning_positions(mock_db_session, mock_user_id):
    """
    Test that find_and_rank_winning_positions correctly identifies and ranks winning positions.
    Ranking rules: highest profit in USD.
    """
    # Mock PositionGroup instances
    pg_winner1 = MagicMock(spec=PositionGroup)
    pg_winner1.id = UUID('55555555-5555-5555-5555-555555555555')
    pg_winner1.created_at = datetime.utcnow() - timedelta(days=2)
    pg_winner1.unrealized_pnl_percent = Decimal("5.0")
    pg_winner1.unrealized_pnl_usd = Decimal("500.0") # Lower USD profit

    pg_winner2 = MagicMock(spec=PositionGroup)
    pg_winner2.id = UUID('66666666-6666-6666-6666-666666666666')
    pg_winner2.created_at = datetime.utcnow() - timedelta(days=1)
    pg_winner2.unrealized_pnl_percent = Decimal("3.0")
    pg_winner2.unrealized_pnl_usd = Decimal("1000.0") # Higher USD profit

    pg_loser = MagicMock(spec=PositionGroup)
    pg_loser.id = UUID('77777777-7777-7777-7777-777777777777')
    pg_loser.created_at = datetime.utcnow() - timedelta(days=7)
    pg_loser.unrealized_pnl_percent = Decimal("-2.0")
    pg_loser.unrealized_pnl_usd = Decimal("-200.0")

    # Mock the database query to return only the winning position groups after filtering
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        pg_winner1, pg_winner2
    ]

    engine = RiskEngine(mock_db_session)
    winning_positions = await engine.find_winning_positions(mock_user_id)

    # Assertions
    mock_db_session.query.assert_called_once_with(PositionGroup)
    mock_db_session.query.return_value.filter.assert_called_once_with(ANY, ANY, ANY) # Filter by user_id, status, and pnl_percent

    # Expected order: pg_winner2 (highest USD profit), pg_winner1 (next highest USD profit)
    assert len(winning_positions) == 2
    assert winning_positions[0] == pg_winner2
    assert winning_positions[1] == pg_winner1
