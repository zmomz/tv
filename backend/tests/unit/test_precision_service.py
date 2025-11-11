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
    """Mocks an async Redis client with awaitable methods."""
    mock = AsyncMock(spec=redis.Redis)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    return mock

@pytest.fixture
def mock_exchange_manager_instance():
    """Mocks the instance that the async context manager will yield."""
    mock_instance = AsyncMock(spec=ExchangeManager)
    mock_instance.get_precision_rules.return_value = {
        'price_precision': 2,
        'amount_precision': 6
    }
    return mock_instance

# This is the standard, robust way to mock an async context manager
class MockAsyncContextManager:
    def __init__(self, mock_instance_to_yield):
        self.mock_instance = mock_instance_to_yield

    async def __aenter__(self):
        return self.mock_instance

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.mark.asyncio
async def test_get_precision_from_cache(mock_redis_client, mock_db_session):
    """
    Test that get_precision returns cached data and does NOT call the exchange.
    """
    settings.PRECISION_CACHE_EXPIRY_SECONDS = 3600
    cached_data = '{"price_precision": 4, "amount_precision": 8}'
    mock_redis_client.get.return_value = cached_data

    service = PrecisionService(mock_redis_client)
    
    with patch('backend.app.services.precision_service.get_exchange') as mock_get_exchange:
        result = await service.get_precision(mock_db_session, "binance", "BTC/USDT")

        assert result == {"price_precision": 4, "amount_precision": 8}
        mock_redis_client.get.assert_awaited_once_with("precision:binance:BTC/USDT")
        mock_get_exchange.assert_not_called()

@pytest.mark.asyncio
async def test_get_precision_fetch_if_no_cache(mock_redis_client, mock_db_session, mock_exchange_manager_instance):
    """
    Test that get_precision fetches from the exchange when cache is empty.
    """
    settings.PRECISION_CACHE_EXPIRY_SECONDS = 3600
    service = PrecisionService(mock_redis_client)

    # The function get_exchange is an async def, so its mock must be an AsyncMock
    # that returns our context manager helper.
    mock_context_manager = MockAsyncContextManager(mock_exchange_manager_instance)
    
    with patch('backend.app.services.precision_service.get_exchange', new_callable=AsyncMock, return_value=mock_context_manager) as mock_get_exchange:
        result = await service.get_precision(mock_db_session, "binance", "BTC/USDT")

        assert result == {"price_precision": 2, "amount_precision": 6}
        mock_redis_client.get.assert_awaited_once_with("precision:binance:BTC/USDT")
        mock_get_exchange.assert_awaited_once_with(mock_db_session, "binance", UUID('00000000-0000-0000-0000-000000000001'))
        mock_exchange_manager_instance.get_precision_rules.assert_awaited_once_with("BTC/USDT")
        mock_redis_client.set.assert_awaited_once()

@pytest.mark.asyncio
async def test_fetch_and_cache_precision_rules(mock_redis_client, mock_db_session, mock_exchange_manager_instance):
    """
    Test that fetch_and_cache_precision_rules directly calls the exchange and caches.
    """
    settings.PRECISION_CACHE_EXPIRY_SECONDS = 3600
    service = PrecisionService(mock_redis_client)

    mock_context_manager = MockAsyncContextManager(mock_exchange_manager_instance)

    with patch('backend.app.services.precision_service.get_exchange', new_callable=AsyncMock, return_value=mock_context_manager) as mock_get_exchange:
        result = await service.fetch_and_cache_precision_rules(mock_db_session, "binance", "BTC/USDT")

        assert result == {"price_precision": 2, "amount_precision": 6}
        mock_get_exchange.assert_awaited_once_with(mock_db_session, "binance", UUID('00000000-0000-0000-0000-000000000001'))
        mock_exchange_manager_instance.get_precision_rules.assert_awaited_once_with("BTC/USDT")
        mock_redis_client.set.assert_awaited_once()

@pytest.mark.asyncio
async def test_fetch_and_cache_precision_rules_handles_exception(mock_redis_client, mock_db_session, mock_exchange_manager_instance):
    """
    Test that fetch_and_cache_precision_rules handles exceptions gracefully.
    """
    mock_exchange_manager_instance.get_precision_rules.side_effect = Exception("Exchange API error")
    mock_context_manager = MockAsyncContextManager(mock_exchange_manager_instance)

    with patch('backend.app.services.precision_service.get_exchange', new_callable=AsyncMock, return_value=mock_context_manager):
        service = PrecisionService(mock_redis_client)
        result = await service.fetch_and_cache_precision_rules(mock_db_session, "binance", "BTC/USDT")
        
        assert result is None
        mock_redis_client.set.assert_not_awaited()

@pytest.mark.asyncio
async def test_get_redis_client():
    """
    Test that get_redis_client returns a Redis client instance and memoizes it.
    """
    settings.REDIS_URL = "redis://localhost:6379/0"
    
    with patch('backend.app.services.precision_service.redis_client', None):
        with patch('redis.asyncio.Redis.from_url', new_callable=AsyncMock) as mock_from_url:
            mock_redis_instance = AsyncMock(spec=redis.Redis)
            mock_from_url.return_value = mock_redis_instance

            client1 = await get_redis_client()
            client2 = await get_redis_client()

            assert client1 == mock_redis_instance
            assert client2 == mock_redis_instance
            mock_from_url.assert_awaited_once_with(settings.REDIS_URL, decode_responses=True)