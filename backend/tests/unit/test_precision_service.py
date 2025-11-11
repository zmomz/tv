import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID
import redis.asyncio as redis
from sqlalchemy.orm import Session

from backend.app.services.precision_service import PrecisionService, get_redis_client
from backend.app.core.config import settings
from backend.app.services.exchange_manager import ExchangeManager

@pytest.fixture
def mock_db_session():
    """Mocks a SQLAlchemy database session."""
    return MagicMock(spec=Session)

@pytest.fixture
def mock_redis_client():
    """Mocks an async Redis client."""
    mock = AsyncMock(spec=redis.Redis)
    # Default return_value for get is None, representing a cache miss.
    mock.get.return_value = None
    return mock

@pytest.fixture
def mock_exchange_manager_instance():
    """Mocks the instance of ExchangeManager that the context manager will return."""
    mock_instance = AsyncMock(spec=ExchangeManager)
    mock_instance.get_precision_rules.return_value = {
        'amount': 8,
        'price': 2,
        'min_amount': 0.001,
        'min_notional': 10
    }
    return mock_instance

@pytest.fixture
def mock_get_exchange(mock_exchange_manager_instance):
    """
    Mocks the get_exchange function.
    This is a two-level mock:
    1. We patch the `get_exchange` function.
    2. The patched function is an AsyncMock that, when called, returns
       another AsyncMock (`mock_context_manager`).
    3. The `mock_context_manager` is what the `async with` statement uses.
       Its `__aenter__` method returns the final `mock_exchange_manager_instance`.
    """
    # This is the object that will act as the async context manager
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_exchange_manager_instance

    # We patch the get_exchange function in the precision_service module
    with patch('backend.app.services.precision_service.get_exchange', new_callable=AsyncMock) as mock_get_exchange_func:
        # Configure the patched function to return our context manager mock
        mock_get_exchange_func.return_value = mock_context_manager
        yield mock_get_exchange_func


@pytest.mark.asyncio
async def test_get_precision_from_cache(mock_redis_client, mock_db_session, mock_get_exchange):
    """
    Test that get_precision retrieves from cache if available and does NOT call the exchange.
    """
    settings.PRECISION_CACHE_EXPIRY_SECONDS = 3600
    service = PrecisionService(mock_redis_client)
    exchange = "binance"
    symbol = "BTC/USDT"
    cached_data = {'amount': 8, 'price': 2, 'min_amount': 0.001, 'min_notional': 10}
    
    # Configure the mock to return cached data
    mock_redis_client.get.return_value = json.dumps(cached_data)

    result = await service.get_precision(mock_db_session, exchange, symbol)

    # Assert that Redis was called
    mock_redis_client.get.assert_awaited_once_with(f"precision:{exchange}:{symbol}")
    
    # Assert that the exchange was NOT called
    mock_get_exchange.assert_not_called()
    
    # Assert the result is correct
    assert result == cached_data

@pytest.mark.asyncio
async def test_get_precision_fetch_if_no_cache(mock_redis_client, mock_db_session, mock_get_exchange, mock_exchange_manager_instance):
    """
    Test that get_precision fetches from the exchange if not in cache.
    """
    settings.PRECISION_CACHE_EXPIRY_SECONDS = 3600
    service = PrecisionService(mock_redis_client)
    exchange = "binance"
    symbol = "BTC/USDT"
    
    # mock_redis_client.get.return_value is already None by default

    result = await service.get_precision(mock_db_session, exchange, symbol)

    # Assert that Redis 'get' was called
    mock_redis_client.get.assert_awaited_once_with(f"precision:{exchange}:{symbol}")
    
    # Assert that the exchange was called
    mock_get_exchange.assert_awaited_once_with(mock_db_session, exchange, UUID('00000000-0000-0000-0000-000000000001'))
    mock_exchange_manager_instance.get_precision_rules.assert_awaited_once_with(symbol)
    
    # Assert that Redis 'set' was called to cache the new data
    mock_redis_client.set.assert_awaited_once()
    
    # Assert the result is correct
    assert result == {'amount': 8, 'price': 2, 'min_amount': 0.001, 'min_notional': 10}

@pytest.mark.asyncio
async def test_fetch_and_cache_precision_rules(mock_redis_client, mock_db_session, mock_get_exchange, mock_exchange_manager_instance):
    """
    Test that fetch_and_cache_precision_rules directly calls the exchange and caches.
    """
    settings.PRECISION_CACHE_EXPIRY_SECONDS = 3600
    service = PrecisionService(mock_redis_client)
    exchange = "binance"
    symbol = "BTC/USDT"

    result = await service.fetch_and_cache_precision_rules(mock_db_session, exchange, symbol)

    # Assert that the exchange was called
    mock_get_exchange.assert_awaited_once_with(mock_db_session, exchange, UUID('00000000-0000-0000-0000-000000000001'))
    mock_exchange_manager_instance.get_precision_rules.assert_awaited_once_with(symbol)

    # Assert that Redis 'set' was called
    mock_redis_client.set.assert_awaited_once()

    # Assert the result is correct
    assert result == {'amount': 8, 'price': 2, 'min_amount': 0.001, 'min_notional': 10}

@pytest.mark.asyncio
async def test_get_redis_client():
    """
    Test that get_redis_client returns a Redis client instance and memoizes it.
    """
    settings.REDIS_URL = "redis://localhost:6379/0"
    
    # Need to reset the global redis_client for this test
    with patch('backend.app.services.precision_service.redis_client', None):
        with patch('redis.asyncio.Redis.from_url', new_callable=AsyncMock) as mock_from_url:
            mock_redis_instance = AsyncMock(spec=redis.Redis)
            mock_from_url.return_value = mock_redis_instance

            client1 = await get_redis_client()
            client2 = await get_redis_client()

            assert client1 == mock_redis_instance
            assert client2 == mock_redis_instance
            
            # Assert that from_url was only called once
            mock_from_url.assert_awaited_once_with(settings.REDIS_URL, decode_responses=True)