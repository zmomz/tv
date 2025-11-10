import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_exchange_api(mocker):
    """
    Mock all exchange API calls.
    """
    mocker.patch("ccxt.async_support.Exchange.fetch_balance", return_value={})
    mocker.patch("ccxt.async_support.Exchange.create_order", return_value={})
    mocker.patch("ccxt.async_support.Exchange.cancel_order", return_value=True)
    mocker.patch("ccxt.async_support.Exchange.fetch_order", return_value={})
    mocker.patch("ccxt.async_support.Exchange.load_markets", return_value={})
    mocker.patch("ccxt.async_support.Exchange.market", return_value={"precision": {}})

@pytest.fixture
def test_user():
    """
    Create a test user with the 'trader' role.
    """
    from app.models.user_models import User
    return User(
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        role="trader",
    )

@pytest.fixture
def test_position_group():
    """
    Create a sample position group.
    """
    from app.models.trading_models import PositionGroup
    return PositionGroup(
        exchange="binance",
        symbol="BTC/USDT",
        timeframe="1h",
        status="waiting",
        entry_signal={},
    )

@pytest.fixture
def mock_webhook_payload():
    """
    Sample TradingView webhook data.
    """
    return {
        "exchange": "binance",
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "entry_price": 50000,
        "total_risk_usd": 1000,
        "dca_config": {
            "dca_levels": 3,
            "price_gaps": [0.01, 0.02, 0.03],
            "dca_weights": [0.25, 0.5, 0.25],
        },
    }
