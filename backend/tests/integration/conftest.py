import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import os

# Add the project root to the path to allow for absolute imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.db.base import Base
from app.core.config import settings
from app.dependencies import get_db
from app.schemas.auth_schemas import UserCreate
from app.services.auth_service import create_user
from main import app

# Import all models to ensure they are registered with Base.metadata
from app.models import user_models, trading_models, key_models, log_models, risk_analytics_models


# Use a separate test database
TEST_DATABASE_URL = str(settings.DATABASE_URL) + "_test"


@pytest.fixture(scope="session")
def db_engine():
    """
    Creates a test database, creates all tables, and yields an engine to it.
    """
    # Connect to the default postgres database to create the test database
    db_name = settings.DATABASE_URL.split("/")[-1]
    default_db_url = settings.DATABASE_URL.replace(db_name, "postgres")
    default_engine = create_engine(default_db_url)

    with default_engine.connect() as conn:
        conn.execute(text("COMMIT"))  # End any existing transactions
        conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}_test"))
        conn.execute(text(f"CREATE DATABASE {db_name}_test"))

    # Now connect to the test database
    engine = create_engine(TEST_DATABASE_URL)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Teardown: drop all tables and the test database
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    with default_engine.connect() as conn:
        conn.execute(text("COMMIT"))
        # Terminate all connections to the test database
        conn.execute(text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_name}_test'
              AND pid <> pg_backend_pid();
        """))
        conn.execute(text(f"DROP DATABASE {db_name}_test"))
    default_engine.dispose()


@pytest.fixture(scope="function")
def client(db_engine):
    """
    Creates a FastAPI TestClient that uses a single transaction for the
    entire test. The transaction is rolled back after the test is finished.
    
    Also provides the transactional session to the test.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client, session
        test_client.close()

    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()
    connection.close()



