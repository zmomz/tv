import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
from unittest.mock import AsyncMock
from datetime import datetime

from app.db.base import Base
from app.core.config import settings
from main import app
from app.db.session import get_async_db

# Ensure the database URL uses the asyncpg driver for tests
settings.DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

@pytest.fixture(scope="session")
def event_loop():
    """Overrides pytest-asyncio's event_loop fixture to be session-scoped."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    """
    Creates a test database engine once per session, creates all tables,
    and drops them after the session ends. This is an async_generator.
    """
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(db_engine):
    """
    Consumes the `db_engine` async_generator to create a transaction-wrapped
    session for each test function. This is also an async_generator.
    """
    async for engine in db_engine:
        connection = await engine.connect()
        transaction = await connection.begin()
        
        Session = sessionmaker(
            bind=connection, class_=AsyncSession, expire_on_commit=False
        )
        session = Session()
        
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()
            await connection.close()

@pytest.fixture(scope="function")
async def client():
    """
    Provides a TestClient for the FastAPI application. Test functions that
    require database access are responsible for overriding the `get_async_db`
    dependency with the correct `db_session`.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def mock_exchange_api():
    """
    Mocks the ccxt exchange API for testing purposes.
    """
    mock_exchange = AsyncMock()
    mock_exchange.create_order.return_value = {
        'id': 'test_order_id',
        'status': 'open',
        'symbol': 'BTC/USDT',
        'type': 'limit',
        'side': 'buy',
        'price': 10000,
        'amount': 0.001,
        'filled': 0,
        'remaining': 0.001,
        'cost': 0,
        'fee': {},
        'datetime': datetime.utcnow().isoformat(),
        'timestamp': datetime.utcnow().timestamp() * 1000,
    }
    mock_exchange.fetch_balance.return_value = {
        'free': {'USDT': 1000},
        'used': {'USDT': 0},
        'total': {'USDT': 1000},
    }
    mock_exchange.fetch_ticker.return_value = {
        'symbol': 'BTC/USDT',
        'last': 29000,
        'bid': 28999,
        'ask': 29001,
    }
    mock_exchange.fetch_order.return_value = {
        'id': 'test_order_id',
        'status': 'closed',
        'symbol': 'BTC/USDT',
        'type': 'limit',
        'side': 'buy',
        'price': 10000,
        'amount': 0.001,
        'filled': 0.001,
        'remaining': 0,
        'cost': 10,
        'fee': {},
        'datetime': datetime.utcnow().isoformat(),
        'timestamp': datetime.utcnow().timestamp() * 1000,
    }
    return mock_exchange
