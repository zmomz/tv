import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.core.config import settings

settings.DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

@pytest.fixture(scope="session")
def event_loop():
    """Overrides pytest-asyncio's event_loop fixture to be session-scoped."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    """Creates a test database and yields an engine to it."""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(db_engine):
    """Creates a new database session for a test."""
    connection = await db_engine.connect()
    trans = await connection.begin()
    Session = sessionmaker(connection, class_=AsyncSession, expire_on_commit=False)
    session = Session()
    yield session
    await session.close()
    await trans.rollback()
    await connection.close()