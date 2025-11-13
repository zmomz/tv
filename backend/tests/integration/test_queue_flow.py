import pytest
from unittest.mock import patch, AsyncMock
from app.schemas.auth_schemas import UserCreate
from app.services.auth_service import create_user
from app.models.key_models import ExchangeConfig
from app.models.trading_models import PositionGroup, QueuedSignal, PositionGroupStatus
from app.services.queue_service import promote_from_queue
from app.core.config import settings
from app.services.jwt_service import create_access_token
from sqlalchemy import select

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

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
async def test_pool_full_queues_signal_and_promotes(client: AsyncClient, db_session: AsyncSession, mock_exchange_api):
    """
    Test the full queueing and promotion flow.
    """
    # 1. client and db_session are now passed directly as fixtures

    # 2. Arrange: Create a user and set the pool size to 1
    async for session in db_session:
        user_in = UserCreate(
            username="queue_user",
            email="queue@test.com",
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

        # 3. Arrange: Fill the execution pool
        with patch('app.core.config.settings', settings.copy(update={'POOL_MAX_OPEN_GROUPS': 1})):
            # Create a live position to fill the pool
            live_position = PositionGroup(
                user_id=test_user.id,
                symbol="ETH/USDT",
                status=PositionGroupStatus.LIVE,
                timeframe=5,
                entry_signal={'action': 'buy'}
            )
            session.add(live_position)
            await session.flush()

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
                response = await client.post(webhook_url, json=webhook_payload, headers=headers)

            # 5. Assert 1: Verify that a QueuedSignal is created
            assert response.status_code == 200
            assert response.json()["status"] == "success"
            
            assert "queued_signal_id" in response.json() # Changed from group_id

            # 6. Act 2 (Promotion): Close the initial position and trigger promotion
            live_position.status = PositionGroupStatus.CLOSED
            await session.flush()

            await promote_from_queue(session, test_user.id)

            # 7. Assert 2: Verify that the QueuedSignal is removed and a new PositionGroup is created
            await session.refresh(live_position)
            promoted_position_result = await session.execute(select(PositionGroup).filter(PositionGroup.symbol == "BTC/USDT"))
            promoted_position = promoted_position_result.scalars().first()
            assert promoted_position is not None
            assert promoted_position.status == PositionGroupStatus.LIVE

            queue_entry_after_promotion_result = await session.execute(select(QueuedSignal))
            queue_entry_after_promotion = queue_entry_after_promotion_result.scalars().first()
            assert queue_entry_after_promotion is None
        break