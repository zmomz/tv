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
from main import app
from app.db.session import get_async_db

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
async def test_signal_queues_when_pool_is_full(client: AsyncClient, db_session: AsyncSession):
    """
    Test that a new signal is added to the queue when the execution pool is full.
    """
    async for session in db_session:
        # 1. Arrange: Create a user and fill the execution pool
        user_in = UserCreate(username="queue_user", email="queue@test.com", password="Password123", role="trader")
        test_user = await create_user(session, user_in)
        await session.commit()

        live_position = PositionGroup(user_id=test_user.id, symbol="ETH/USDT", status=PositionGroupStatus.LIVE, timeframe=5, entry_signal={'action': 'buy'})
        session.add(live_position)
        await session.commit()

        # 2. Act: Send a new webhook signal with the pool maxed out
        with patch('app.core.config.settings.POOL_MAX_OPEN_GROUPS', 1):
            webhook_payload = {
                "secret": settings.WEBHOOK_SECRET,
                "tv": {"symbol": "BTC/USDT", "exchange": "binance", "timeframe": "5m"},
                "execution_intent": {"action": "buy", "amount": 0.001, "strategy": "grid"}
            }
            webhook_url = f"/api/webhook/webhook/{test_user.id}"
            
            app.dependency_overrides[get_async_db] = lambda: session
            access_token = create_access_token(user_id=test_user.id, email=test_user.email, role=test_user.role)
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = await client.post(webhook_url, json=webhook_payload, headers=headers)
            app.dependency_overrides.clear()

        # 3. Assert: Verify that a QueuedSignal was created
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "queued_signal_id" in response.json()

        result = await session.execute(select(QueuedSignal).filter(QueuedSignal.user_id == test_user.id))
        queued_signal = result.scalars().first()
        assert queued_signal is not None
        assert queued_signal.symbol == "BTC/USDT"

@pytest.mark.asyncio
async def test_promote_from_queue_prioritizes_correctly(db_session: AsyncSession):
    """
    Test that the promote_from_queue function correctly selects the highest priority signal.
    """
    async for session in db_session:
        # 1. Arrange: Create a user and multiple queued signals with different priorities
        user_in = UserCreate(username="promote_user", email="promote@test.com", password="Password123", role="trader")
        test_user = await create_user(session, user_in)
        await session.flush()

        # Lower priority signal
        session.add(QueuedSignal(user_id=test_user.id, symbol="BTC/USDT", priority_score=10, replacement_count=0, original_signal={}))
        # Highest priority signal (higher score)
        session.add(QueuedSignal(user_id=test_user.id, symbol="ETH/USDT", priority_score=20, replacement_count=0, original_signal={}))
        # Higher priority signal (same score, more replacements)
        session.add(QueuedSignal(user_id=test_user.id, symbol="XRP/USDT", priority_score=20, replacement_count=1, original_signal={}))
        await session.flush()

        # 2. Act: Call the promotion function
        promoted_signal = await promote_from_queue(session, test_user.id)

        # 3. Assert: Verify that the correct signal was promoted and removed from the queue
        assert promoted_signal is not None
        assert promoted_signal.symbol == "XRP/USDT"

        result = await session.execute(select(QueuedSignal).filter(QueuedSignal.user_id == test_user.id))
        remaining_signals = result.scalars().all()
        assert len(remaining_signals) == 2
        assert "XRP/USDT" not in [s.symbol for s in remaining_signals]
