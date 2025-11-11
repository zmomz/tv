import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session

from backend.app.services.validation_service import validate_and_adjust_order
from backend.app.services import precision_service, exchange_manager

@pytest.fixture
def mock_db_session():
    """Mocks a SQLAlchemy database session."""
    return MagicMock(spec=Session)

@pytest.fixture
def mock_precision_info():
    """Mocks the precision information returned by precision_service."""
    return {
        'amount': 8,  # 8 decimal places for quantity
        'price': 2,   # 2 decimal places for price
        'min_amount': 0.001,
        'min_notional': 10
    }

@pytest.mark.asyncio
async def test_validate_and_adjust_order_success(mock_db_session, mock_precision_info):
    """
    Test successful validation and adjustment of order parameters.
    """
    exchange = "binance"
    symbol = "BTC/USDT"
    side = "buy"
    quantity = Decimal("0.123456789")
    price = Decimal("50000.123")

    with patch('backend.app.services.precision_service.fetch_precision_info', new_callable=AsyncMock) as mock_fetch_precision_info:
        mock_fetch_precision_info.return_value = mock_precision_info
        
        # Mock ccxt.decimal_to_precision directly
        with patch('backend.app.services.exchange_manager.ccxt.decimal_to_precision') as mock_decimal_to_precision:
            mock_decimal_to_precision.side_effect = lambda num, rounding_mode, precision: Decimal(f"{num:.{precision}f}")

            adjusted_quantity, adjusted_price = await validate_and_adjust_order(
                mock_db_session, exchange, symbol, side, quantity, price
            )

            mock_fetch_precision_info.assert_awaited_once_with(mock_db_session, exchange, symbol)
            assert adjusted_quantity == Decimal("0.12345679") # Rounded to 8 decimal places
            assert adjusted_price == Decimal("50000.12")    # Rounded to 2 decimal places

@pytest.mark.asyncio
async def test_validate_and_adjust_order_missing_precision(mock_db_session):
    """
    Test that ValueError is raised if precision data is missing.
    """
    exchange = "binance"
    symbol = "BTC/USDT"
    side = "buy"
    quantity = Decimal("0.1")
    price = Decimal("50000")

    with patch('backend.app.services.precision_service.fetch_precision_info', new_callable=AsyncMock) as mock_fetch_precision_info:
        mock_fetch_precision_info.return_value = None # Simulate missing precision

        with pytest.raises(ValueError, match=f"Precision rules not available for {exchange}:{symbol}. Cannot validate order."):
            await validate_and_adjust_order(
                mock_db_session, exchange, symbol, side, quantity, price
            )
        mock_fetch_precision_info.assert_awaited_once_with(mock_db_session, exchange, symbol)

# TODO: Add tests for minimum notional value once implemented in validation_service.py
