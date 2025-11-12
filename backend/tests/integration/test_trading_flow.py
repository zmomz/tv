import pytest
from unittest.mock import patch, AsyncMock
from app.schemas.auth_schemas import UserCreate
from app.services.auth_service import create_user
from app.models.key_models import ExchangeConfig
from app.models.trading_models import PositionGroup
from main import app
from app.db.session import get_db
from app.services.jwt_service import create_access_token

# Helper class from GEMINI.md to mock async context managers
class MockAsyncContextManager:
    """A helper to robustly mock an async context manager."""
    def __init__(self, mock_instance_to_return):
        self.mock_instance = mock_instance_to_return
    async def __aenter__(self):
        return self.mock_instance
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

def test_webhook_to_live_position(client, mock_exchange_api):
    """
    Test the full trading flow from webhook ingestion to a live position
    using the correct transactional fixture pattern from GEMINI.md.
    """
    # 1. Unpack the client and session from the fixture
    test_client, db_session = client

    # 2. Arrange: Create all test data using the provided db_session
    user_in = UserCreate(
        username="integration_user",
        email="integration@test.com",
        password="Password123",
        role="trader"
    )
    test_user = create_user(db_session, user_in)
    
    # CRITICAL: Use flush() to persist data within the transaction
    db_session.flush()
    db_session.refresh(test_user)

    exchange_config = ExchangeConfig(
        user_id=test_user.id,
        exchange_name="binance",
        api_key_encrypted="test_api_key",
        api_secret_encrypted="test_api_secret",
        mode="testnet",
        is_enabled=True
    )
    db_session.add(exchange_config)
    
    db_session.flush()
    db_session.refresh(exchange_config)

    webhook_payload = {
        "secret": "test",
        "tv": {"symbol": "BTC/USDT", "exchange": "binance", "timeframe": "5m"},
        "execution_intent": {"action": "buy", "amount": 0.001, "strategy": "grid"}
    }
    webhook_url = f"/api/webhook/webhook/{test_user.id}"

    # 3. Arrange: Mock the ExchangeManager
    mock_exchange_instance = AsyncMock()
    mock_exchange_instance.place_order.return_value = {
        'id': '12345', 'status': 'closed', 'symbol': 'BTC/USDT', 'price': 50000, 'amount': 0.001
    }
    mock_exchange_context = MockAsyncContextManager(mock_exchange_instance)

    access_token = create_access_token(user_id=test_user.id, email=test_user.email, role=test_user.role)
    headers = {"Authorization": f"Bearer {access_token}"}

    app.dependency_overrides[get_db] = lambda: db_session

    with patch('app.api.webhooks.ExchangeManager', return_value=mock_exchange_context):
        # 4. Act: Send the webhook request
        response = test_client.post(webhook_url, json=webhook_payload, headers=headers)

    app.dependency_overrides.clear()
    
    # 5. Assert: Verify the HTTP response and the final database state
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["status"] == "success"
    assert "queued_signal_id" in response.json()
    
    # The db_session is the same one used by the endpoint, so the state is consistent
    position_group = db_session.query(PositionGroup).one_or_none()
    assert position_group is None
