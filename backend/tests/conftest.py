import pytest
from unittest.mock import MagicMock
import os
import sys
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to the path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from app.db.session import get_db
from app.db.base import Base
from app.core.config import settings

# Import all models to ensure they are registered with Base.metadata
from app.models import user_models, trading_models, key_models, log_models, risk_analytics_models
from app.models.user_models import User

@pytest.fixture(scope="session")
def db_engine():
    """
    Creates a test database with a random name, creates all tables, and yields an engine to it.
    """
    db_name = f"test_db_{uuid.uuid4().hex}"
    
    # Connect to default postgres to create test database
    default_db_url = str(settings.DATABASE_URL).replace(settings.DATABASE_URL.split("/")[-1], "postgres")
    default_engine = create_engine(default_db_url, isolation_level="AUTOCOMMIT")
    
    with default_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE {db_name}"))
    
    # Now connect to the test database
    engine = create_engine(str(settings.DATABASE_URL).replace(settings.DATABASE_URL.split("/")[-1], db_name))
    
    Base.metadata.create_all(bind=engine)

    yield engine

    # Teardown: drop all tables and the test database
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    
    with default_engine.connect() as conn:
        # Terminate all connections to the test database
        conn.execute(text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_name}'
              AND pid <> pg_backend_pid();
        """))
        conn.execute(text(f"DROP DATABASE {db_name}"))
    default_engine.dispose()

@pytest.fixture(scope="function")
def client(db_engine):
    """
    Creates a FastAPI TestClient that uses a single, shared transaction
    for the entire test. The transaction is rolled back after the test is
    finished, ensuring a clean state.

    This fixture yields both the TestClient and the transactional session.
    """
    # 1. Establish a connection and begin a transaction
    connection = db_engine.connect()
    transaction = connection.begin()

    # 2. Create a session bound to this transaction
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()

    # 3. Override the app's database dependency to use our transactional session
    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    # 4. Yield the client and session to the test
    with TestClient(app) as test_client:
        yield test_client, session

    # 5. Teardown: clean up everything
    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()  # Roll back the transaction to isolate the test
    connection.close()

@pytest.fixture
def mock_exchange_api(mocker):
    """
    Mock all exchange API calls.
    """
    mocker.patch("ccxt.async_support.Exchange.fetch_balance", return_value={})
    mocker.patch("ccxt.async_support.Exchange.create_order", return_value={})
    mocker.patch("ccxt.async_support.Exchange.cancel_order", return_value=True)
    mocker.patch("ccxt.async_support.Exchange.fetch_order", return_value={})
    mocker.patch("ccxt.async_support.Exchange.load_markets", return_value={})
    mocker.patch("ccxt.async_support.Exchange.market", return_value={"precision": {}})
