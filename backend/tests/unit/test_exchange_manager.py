import pytest
from unittest.mock import MagicMock, AsyncMock
import unittest
from uuid import uuid4
from decimal import Decimal
from backend.app.services.exchange_manager import ExchangeManager

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def mock_exchange_config():
    return {
        'api_key_encrypted': b'encrypted_api_key',
        'api_secret_encrypted': b'encrypted_api_secret',
        'mode': 'testnet'
    }

@pytest.mark.asyncio
async def test_exchange_manager_initialization(mock_db_session, mock_exchange_config):
    user_id = uuid4()
    exchange_name = 'binance'

    mock_db_session.query.return_value.filter.return_value.first.return_value = MagicMock(
        **mock_exchange_config
    )

    with unittest.mock.patch('backend.app.services.encryption_service.decrypt_data') as mock_decrypt:
        mock_decrypt.side_effect = ['test_api_key', 'test_api_secret']
        
        async with ExchangeManager(mock_db_session, user_id, exchange_name) as em:
            assert em.exchange is not None
            # Further assertions can be made here

# Add more tests for other methods in ExchangeManager
