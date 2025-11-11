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
        conn.execute(text(f"DROP DATABASE {settings.DATABASE_URL.path[1:]}_test"))
    default_engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Creates a new database session for each test, wrapped in a transaction.
    """
    connection = db_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Creates a new FastAPI TestClient for each test.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

