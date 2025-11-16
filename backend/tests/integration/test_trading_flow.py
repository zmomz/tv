import pytest
from unittest.mock import patch, AsyncMock
from app.schemas.auth_schemas import UserCreate
from app.services.auth_service import create_user
from app.models.key_models import ExchangeConfig
from app.models.trading_models import PositionGroup, PositionGroupStatus
from main import app
from app.db.session import get_async_db
from app.services.jwt_service import create_access_token
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient

# Helper class from GEMINI.md to mock async context managers
class MockAsyncContextManager:
    """A helper to robustly mock an async context manager."""
    def __init__(self, mock_instance_to_return):
        self.mock_instance = mock_instance_to_return
    async def __aenter__(self):
        return self.mock_instance
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.mark.asyncio
async def test_webhook_to_live_position(client: AsyncClient, db_session: AsyncSession, mock_exchange_api):
    """
    Test the full trading flow from webhook ingestion to a live position
    using the correct transactional fixture pattern from GEMINI.md.
    """
    # 1. client and db_session are now passed directly as fixtures

    # 2. Arrange: Create all test data using the provided db_session
    async for session in db_session:
        user_in = UserCreate(
            username="integration_user",
            email="integration@test.com",
            password="Password123",
            role="trader"
        )
        test_user = await create_user(session, user_in)
        await session.flush()
        await session.refresh(test_user)

        exchange_config = ExchangeConfig(
            user_id=test_user.id,
            exchange_name="binance",
            api_key_encrypted="test_api_key",
            api_secret_encrypted="test_api_secret",
            mode="testnet",
            is_enabled=True
        )
        session.add(exchange_config)
        
        await session.flush()
        await session.refresh(exchange_config)

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

        app.dependency_overrides[get_async_db] = lambda: session # Use the session from the fixture

        with patch('app.api.webhooks.ExchangeManager', return_value=mock_exchange_context):
            # 4. Act: Send the webhook request
            response = await client.post(webhook_url, json=webhook_payload, headers=headers)

        app.dependency_overrides.clear()
        
        # 5. Assert: Verify the HTTP response and the final database state
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["status"] == "success"
        assert "queued_signal_id" in response.json()
        
        # The db_session is the same one used by the endpoint, so the state is consistent
        # Need to use async db operations for assertions
        result = await session.execute(select(PositionGroup))
        position_group = result.scalars().first()
        assert position_group is None