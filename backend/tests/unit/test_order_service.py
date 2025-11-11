import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session

from backend.app.services.order_service import place_dca_orders, handle_filled_order, cancel_pending_orders, monitor_order_fills
from backend.app.models.trading_models import PositionGroup, DCAOrder
from backend.app.services.exchange_manager import ExchangeManager

# As per GEMINI.md, this is the correct way to mock an async context manager
class MockAsyncContextManager:
    """
    A helper class to robustly mock an async context manager.
    """
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
def mock_position_group():
    """Mocks a PositionGroup instance."""
    pg = MagicMock(spec=PositionGroup)
    pg.id = UUID('12345678-1234-5678-1234-567812345678')
    pg.user_id = UUID('00000000-0000-0000-0000-000000000001')
    pg.exchange = "binance"
    pg.symbol = "BTC/USDT"
    pg.entry_signal = {
        "entry_price": "100.00",
        "total_risk_usd": "1000.00",
        "dca_config": {
            "dca_levels": 2,
            "price_gaps": [Decimal("0.01"), Decimal("0.02")],
            "dca_weights": [Decimal("0.5"), Decimal("0.5")]
        }
    }
    return pg

@pytest.fixture
def mock_exchange_manager():
    """
    Creates a mock ExchangeManager instance that is also a valid async context manager.
    """
    manager = MagicMock(spec=ExchangeManager)
    manager.place_order = AsyncMock()
    manager.cancel_order = AsyncMock()
    manager.fetch_order = AsyncMock() # Add fetch_order mock
    manager.__aenter__ = AsyncMock(return_value=manager)
    manager.__aexit__ = AsyncMock(return_value=None)
    return manager

@pytest.mark.asyncio
async def test_place_dca_orders_successfully(mock_db_session, mock_position_group, mock_exchange_manager):
    """
    Verify that place_dca_orders correctly uses the ExchangeManager to place orders.
    """
    with patch('backend.app.services.order_service.grid_calculator.calculate_dca_levels', return_value=[
        {"price": Decimal("99.00")}, {"price": Decimal("98.00")}
    ]), \
    patch('backend.app.services.order_service.grid_calculator.calculate_position_size', return_value=[
        Decimal("500.00"), Decimal("500.00")
    ]), \
    patch('backend.app.services.order_service.validation_service.validate_and_adjust_order', new_callable=AsyncMock) as mock_validate, \
    patch('backend.app.services.exchange_manager.ExchangeManager', return_value=mock_exchange_manager) as mock_exchange_manager_class:

        mock_validate.side_effect = [
            (Decimal("5.0505"), Decimal("99.00")),
            (Decimal("5.1020"), Decimal("98.00"))
        ]
        mock_exchange_manager.place_order.side_effect = [
            {"id": "order_id_1"}, {"id": "order_id_2"}
        ]

        await place_dca_orders(mock_db_session, mock_position_group)

        mock_exchange_manager_class.assert_called_once_with(mock_db_session, mock_position_group.user_id, "binance")
        mock_exchange_manager.__aenter__.assert_awaited_once()
        assert mock_exchange_manager.place_order.call_count == 2
        mock_exchange_manager.place_order.assert_any_await(
            symbol="BTC/USDT", side="buy", order_type="limit", amount=Decimal("5.0505"), price=Decimal("99.00")
        )
        mock_exchange_manager.__aexit__.assert_awaited_once()
        mock_db_session.commit.assert_called_once()

def test_handle_filled_order_updates_status(mock_db_session):
    dca_order = MagicMock(spec=DCAOrder)
    fill_data = {"price": "99.50", "filled": "5.0"}
    handle_filled_order(mock_db_session, dca_order, fill_data)
    assert dca_order.status == "filled"
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_cancel_pending_orders_successfully(mock_db_session, mock_position_group, mock_exchange_manager):
    order1 = MagicMock(spec=DCAOrder)
    order1.exchange_order_id = "order_id_1"
    order1.position_group = mock_position_group
    mock_db_session.query.return_value.filter.return_value.all.return_value = [order1]

    with patch('backend.app.services.exchange_manager.ExchangeManager', return_value=mock_exchange_manager) as mock_exchange_manager_class:
        await cancel_pending_orders(mock_db_session, mock_position_group.id)

        mock_exchange_manager_class.assert_called_once_with(mock_db_session, mock_position_group.user_id, "binance")
        mock_exchange_manager.__aenter__.assert_awaited_once()
        mock_exchange_manager.cancel_order.assert_awaited_once_with(symbol="BTC/USDT", order_id="order_id_1")
        assert order1.status == "cancelled"
        mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_monitor_order_fills_updates_filled_orders(
    mock_db_session, mock_position_group, mock_exchange_manager
):
    """
    Verify that monitor_order_fills correctly identifies and updates filled orders.
    """
    # Setup: A pending DCA order
    pending_order = MagicMock(spec=DCAOrder)
    pending_order.id = UUID('11111111-1111-1111-1111-111111111111')
    pending_order.exchange_order_id = "pending_order_id"
    pending_order.position_group = mock_position_group
    pending_order.status = "pending"

    mock_db_session.query.return_value.filter.return_value.all.return_value = [pending_order]

    mock_context = MockAsyncContextManager(mock_exchange_manager)
    # Mock the exchange to return a filled status for the pending order
    mock_exchange_manager.fetch_order.return_value = {
        "id": "pending_order_id",
        "status": "closed", # ccxt uses 'closed' for filled orders
        "filled": Decimal("1.0"),
        "price": Decimal("100.00")
    }

    with patch('backend.app.services.exchange_manager.get_exchange', new_callable=AsyncMock) as mock_get_exchange, \
         patch('backend.app.services.order_service.handle_filled_order') as mock_handle_filled_order:
        mock_get_exchange.return_value = mock_context

        await monitor_order_fills(mock_db_session) # Pass db session to the function

        # Assertions
        mock_get_exchange.assert_awaited_once_with(
            mock_db_session,
            mock_position_group.exchange,
            mock_position_group.user_id
        )
        mock_exchange_manager.fetch_order.assert_awaited_once_with(
            order_id="pending_order_id",
            symbol=mock_position_group.symbol
        )
        mock_handle_filled_order.assert_called_once_with(
            mock_db_session,
            pending_order,
            {"id": "pending_order_id", "status": "closed", "filled": Decimal("1.0"), "price": Decimal("100.00")}
        )
        # The status update and commit are handled by handle_filled_order, so we don't assert them here directly