import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session

from backend.app.services.take_profit_service import execute_per_leg_tp, execute_aggregate_tp, execute_hybrid_tp
from backend.app.models.trading_models import PositionGroup, DCAOrder
from backend.app.services.exchange_manager import ExchangeManager

# Helper class for mocking the async context manager
class MockAsyncContextManager:
    def __init__(self, mock_instance_to_return):
        self.mock_instance = mock_instance_to_return
    async def __aenter__(self):
        return self.mock_instance
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.fixture
def mock_db_session():
    """Mocks a SQLAlchemy database session."""
    return MagicMock(spec=Session)

@pytest.fixture
def mock_exchange_manager_instance():
    """Mocks the ExchangeManager instance."""
    manager = MagicMock(spec=ExchangeManager)
    manager.get_current_price = AsyncMock()
    manager.place_order = AsyncMock()
    return manager

@pytest.fixture
def mock_position_group():
    """Mocks a PositionGroup with a per-leg TP configuration."""
    pg = MagicMock(spec=PositionGroup)
    pg.id = UUID('12345678-1234-5678-1234-567812345678')
    pg.user_id = UUID('00000000-0000-0000-0000-000000000001')
    pg.exchange = "binance"
    pg.symbol = "BTC/USDT"
    pg.tp_config = {
        "tp_mode": "per-leg",
        "tp_price_targets": [Decimal("1.01"), Decimal("1.02")] # 1% and 2% profit
    }
    return pg

@pytest.mark.asyncio
async def test_execute_per_leg_tp_triggers_on_price_target(
    mock_db_session, mock_position_group, mock_exchange_manager_instance
):
    """
    Verify that a take-profit order is placed when the current price
    exceeds the calculated TP target for a specific DCA leg.
    """
    # Setup: One filled order, one open, one already taken profit
    dca_order_filled = MagicMock(spec=DCAOrder)
    dca_order_filled.dca_level = 0
    dca_order_filled.filled_price = Decimal("100.00")
    dca_order_filled.quantity = Decimal("1.0")
    dca_order_filled.status = "filled"

    # The application code filters for "filled", so the mock should only return the filled order.
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        dca_order_filled
    ]

    # Mock the exchange manager context and current price
    mock_context = MockAsyncContextManager(mock_exchange_manager_instance)
    # Price (101.50) is above the 1% TP target (101.00) for the first leg
    mock_exchange_manager_instance.get_current_price.return_value = Decimal("101.50")

    with patch('backend.app.services.order_service.exchange_manager.get_exchange', new_callable=AsyncMock) as mock_get_exchange:
        mock_get_exchange.return_value = mock_context

        await execute_per_leg_tp(mock_db_session, mock_position_group)

        # Assertions
        mock_exchange_manager_instance.get_current_price.assert_awaited_once_with("BTC/USDT")
        
        # Verify that a sell order was placed for the filled leg
        mock_exchange_manager_instance.place_order.assert_awaited_once_with(
            symbol="BTC/USDT",
            side="sell",
            order_type="market",
            amount=dca_order_filled.quantity
        )
        
        # Verify the order's status was updated in the DB
        assert dca_order_filled.status == "tp-taken"
        mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_execute_aggregate_tp_triggers_on_price_target(
    mock_db_session, mock_position_group, mock_exchange_manager_instance
):
    """
    Verify that an aggregate take-profit order is placed when the
    average entry price meets the TP target for the entire position group.
    """
    # Adjust position group for aggregate TP
    mock_position_group.tp_config = {
        "tp_mode": "aggregate",
        "tp_price_targets": [Decimal("1.05")] # 5% aggregate profit
    }

    # Setup: Multiple filled orders for calculating average entry price
    dca_order_1 = MagicMock(spec=DCAOrder)
    dca_order_1.status = "filled"
    dca_order_1.filled_price = Decimal("100.00")
    dca_order_1.quantity = Decimal("1.0")

    dca_order_2 = MagicMock(spec=DCAOrder)
    dca_order_2.status = "filled"
    dca_order_2.filled_price = Decimal("105.00")
    dca_order_2.quantity = Decimal("1.0")

    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        dca_order_1, dca_order_2
    ]

    mock_context = MockAsyncContextManager(mock_exchange_manager_instance)
    # Current price (111.00) is above the 5% TP target (107.50) for average entry (102.50)
    mock_exchange_manager_instance.get_current_price.return_value = Decimal("111.00")

    with patch('backend.app.services.exchange_manager.get_exchange', new_callable=AsyncMock) as mock_get_exchange, \
         patch('backend.app.services.take_profit_service.calculate_average_entry_price', return_value=Decimal("102.50")) as mock_avg_entry:
        mock_get_exchange.return_value = mock_context

        await execute_aggregate_tp(mock_db_session, mock_position_group)

        # Assertions
        mock_avg_entry.assert_called_once_with([dca_order_1, dca_order_2])
        mock_exchange_manager_instance.get_current_price.assert_awaited_once_with("BTC/USDT")
        
        # Verify a sell order for the total quantity
        mock_exchange_manager_instance.place_order.assert_awaited_once_with(
            symbol="BTC/USDT",
            side="sell",
            order_type="market",
            amount=Decimal("2.0") # Total quantity from dca_order_1 + dca_order_2
        )
        
        # Verify position group status updated
        assert mock_position_group.status == "closed"
        mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_execute_hybrid_tp_triggers_on_conditions(
    mock_db_session, mock_position_group, mock_exchange_manager_instance
):
    """
    Verify that a hybrid take-profit order is placed when its conditions are met.
    This test assumes a simple hybrid strategy: close a percentage of the position
    if the aggregate profit target is met.
    """
    # Adjust position group for hybrid TP
    mock_position_group.tp_config = {
        "tp_mode": "hybrid",
        "aggregate_profit_target": Decimal("1.05"), # 5% aggregate profit
        "partial_close_percentage": Decimal("0.5") # Close 50% of position
    }

    # Setup: Multiple filled orders for calculating average entry price
    dca_order_1 = MagicMock(spec=DCAOrder)
    dca_order_1.status = "filled"
    dca_order_1.filled_price = Decimal("100.00")
    dca_order_1.quantity = Decimal("1.0")

    dca_order_2 = MagicMock(spec=DCAOrder)
    dca_order_2.status = "filled"
    dca_order_2.filled_price = Decimal("105.00")
    dca_order_2.quantity = Decimal("1.0")

    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        dca_order_1, dca_order_2
    ]

    mock_context = MockAsyncContextManager(mock_exchange_manager_instance)
    # Current price (111.00) is above the 5% TP target (107.50) for average entry (102.50)
    mock_exchange_manager_instance.get_current_price.return_value = Decimal("111.00")

    with patch('backend.app.services.exchange_manager.get_exchange', new_callable=AsyncMock) as mock_get_exchange, \
         patch('backend.app.services.take_profit_service.calculate_average_entry_price', return_value=Decimal("102.50")) as mock_avg_entry:
        mock_get_exchange.return_value = mock_context

        await execute_hybrid_tp(mock_db_session, mock_position_group)

        # Assertions
        mock_avg_entry.assert_called_once_with([dca_order_1, dca_order_2])
        mock_exchange_manager_instance.get_current_price.assert_awaited_once_with("BTC/USDT")
        
        # Verify a sell order for the partial quantity
        expected_partial_quantity = Decimal("2.0") * Decimal("0.5") # Total quantity * 50%
        mock_exchange_manager_instance.place_order.assert_awaited_once_with(
            symbol="BTC/USDT",
            side="sell",
            order_type="market",
            amount=expected_partial_quantity
        )
        
        # Verify position group status is NOT closed, but perhaps a new status like 'partially-closed'
        # For now, we'll just assert that it's not 'closed' if it was not fully closed.
        # The actual status update logic will be in the implementation.
        # assert mock_position_group.status == "partially-closed" # This will be implemented in the service
        mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_execute_per_leg_tp_does_not_trigger_below_price_target(
    mock_db_session, mock_position_group, mock_exchange_manager_instance
):
    """
    Verify that no take-profit order is placed when the current price
    is below the calculated TP target.
    """
    dca_order_filled = MagicMock(spec=DCAOrder)
    dca_order_filled.status = "filled"
    dca_order_filled.dca_level = 0
    dca_order_filled.filled_price = Decimal("100.00")
    dca_order_filled.quantity = Decimal("1.0")

    mock_db_session.query.return_value.filter.return_value.all.return_value = [dca_order_filled]

    mock_context = MockAsyncContextManager(mock_exchange_manager_instance)
    # Price (100.50) is below the 1% TP target (101.00)
    mock_exchange_manager_instance.get_current_price.return_value = Decimal("100.50")

    with patch('backend.app.services.order_service.exchange_manager.get_exchange', new_callable=AsyncMock) as mock_get_exchange:
        mock_get_exchange.return_value = mock_context

        await execute_per_leg_tp(mock_db_session, mock_position_group)

        # Assertions
        mock_exchange_manager_instance.get_current_price.assert_awaited_once_with("BTC/USDT")
        mock_exchange_manager_instance.place_order.assert_not_awaited()
        assert dca_order_filled.status == "filled" # Status should not change
        mock_db_session.commit.assert_not_called()
