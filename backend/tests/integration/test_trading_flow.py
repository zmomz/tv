import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.user_models import User
from app.models.key_models import ExchangeConfig
from app.models.trading_models import PositionGroup, DCAOrder
from app.services.auth_service import create_user
from app.schemas.auth_schemas import UserCreate


@pytest.fixture(scope="function")
def test_user(db_session: Session):
    """
    Creates a test user in the database.
    """
    user_in = UserCreate(
        username="testuser",
        email="test@example.com",
        password="Password123",
        role="trader"
    )
    return create_user(db_session, user_in)

@pytest.fixture(scope="function")
def test_exchange_config(db_session: Session, test_user: User):
    """
    Creates a test exchange configuration in the database.
    """
    exchange_config = ExchangeConfig(
        user_id=test_user.id,
        exchange_name="binance",
        api_key="test_api_key",
        secret_key="test_secret_key"
    )
    db_session.add(exchange_config)
    db_session.commit()
    return exchange_config

def test_webhook_to_live_position(client: TestClient, db_session: Session, test_user: User, test_exchange_config: ExchangeConfig):
    """
    Test the full trading flow from webhook ingestion to a live position.
    """
    # Arrange
    webhook_payload = {
        "secret": "test",
        "tv": {"symbol": "BTC/USDT", "exchange": "binance"},
        "execution_intent": {"action": "buy", "amount": 0.001, "strategy": "grid"}
    }

    # Act
    response = client.post(f"/api/webhook/{test_user.id}", json=webhook_payload)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Webhook received and processed."}

    # Verify database state
    position_group = db_session.query(PositionGroup).one_or_none()
    assert position_group is not None
    assert position_group.user_id == test_user.id
    assert position_group.symbol == "BTC/USDT"
    assert position_group.status == "live"

    dca_orders = db_session.query(DCAOrder).all()
    assert len(dca_orders) > 0
