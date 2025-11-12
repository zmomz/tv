import pytest
from unittest.mock import patch, AsyncMock
from app.schemas.auth_schemas import UserCreate
from app.services.auth_service import create_user
from app.models.key_models import ExchangeConfig
from app.models.trading_models import PositionGroup, QueueEntry, PositionGroupStatus
from app.services.queue_service import promote_from_queue
from app.core.config import settings
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

@pytest.mark.asyncio
async def test_pool_full_queues_signal_and_promotes(client, mock_exchange_api):
    """
    Test the full queueing and promotion flow.
    """
    # 1. Unpack the client and session from the fixture
    test_client, db_session = client

    # 2. Arrange: Create a user and set the pool size to 1
    user_in = UserCreate(
        username="queue_user",
        email="queue@test.com",
        password="Password123",
        role="trader"
    )
    test_user = create_user(db_session, user_in)
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

    # 3. Arrange: Fill the execution pool
    with patch('app.core.config.settings', settings.copy(update={'EXECUTION_POOL_MAX_OPEN_GROUPS': 1})):
        # Create a live position to fill the pool
        live_position = PositionGroup(
            user_id=test_user.id,
            symbol="ETH/USDT",
            status=PositionGroupStatus.open,
            timeframe="5m",
            entry_signal='{"action": "buy"}'
        )
        db_session.add(live_position)
        db_session.flush()

        # 4. Act 1 (Queueing): Send a new webhook signal
        webhook_payload = {
            "secret": "test",
            "tv": {"symbol": "BTC/USDT", "exchange": "binance", "timeframe": "5m"},
            "execution_intent": {"action": "buy", "amount": 0.001, "strategy": "grid"}
        }
        webhook_url = f"/api/webhook/webhook/{test_user.id}"
        
        mock_exchange_instance = AsyncMock()
        mock_exchange_context = MockAsyncContextManager(mock_exchange_instance)

        with patch('app.api.webhooks.ExchangeManager', return_value=mock_exchange_context):
            access_token = create_access_token(user_id=test_user.id, email=test_user.email, role=test_user.role)
            headers = {"Authorization": f"Bearer {access_token}"}
            response = test_client.post(webhook_url, json=webhook_payload, headers=headers)

        # 5. Assert 1: Verify that a QueueEntry is created
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
        assert "group_id" in response.json()

        # 6. Act 2 (Promotion): Close the initial position and trigger promotion
        live_position.status = PositionGroupStatus.closed
        db_session.flush()

        await promote_from_queue(db_session, test_user.id)

        # 7. Assert 2: Verify that the QueueEntry is removed and a new PositionGroup is created
        db_session.refresh(live_position)
        promoted_position = db_session.query(PositionGroup).filter(PositionGroup.symbol == "BTC/USDT").one_or_none()
        assert promoted_position is not None
        assert promoted_position.status == PositionGroupStatus.open

        queue_entry_after_promotion = db_session.query(QueueEntry).one_or_none()
        assert queue_entry_after_promotion is None