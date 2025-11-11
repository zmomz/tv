import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, ANY

from app.models.user_models import User
from app.models.key_models import ExchangeConfig
from app.models.trading_models import PositionGroup, DCAOrder
from app.services.auth_service import create_user
from app.schemas.auth_schemas import UserCreate


def test_webhook_to_live_position(client: TestClient):
    """
    Test the full trading flow from webhook ingestion to a live position.
    """
    client, db_session = client  # Unpack the client and session from the fixture

    # Arrange: Create test user and config within the test's transaction
    user_in = UserCreate(
        username="testuser",
        email="test@example.com",
        password="Password123",
        role="trader"
    )
    test_user = create_user(db_session, user_in)
    db_session.flush()

    exchange_config = ExchangeConfig(
        user_id=test_user.id,
        exchange_name="binance",
        api_key_encrypted="test_api_key",
        api_secret_encrypted="test_api_secret",
        mode="testnet"
    )
    db_session.add(exchange_config)
    db_session.flush()
    db_session.refresh(test_user) # Refresh to get user.id

    webhook_payload = {
        "secret": "test",
        "tv": {"symbol": "BTC/USDT", "exchange": "binance"},
        "execution_intent": {"action": "buy", "amount": 0.001, "strategy": "grid"}
    }
    webhook_url = f"/api/webhook/{test_user.id}"

    # Mock the exchange manager to prevent real API calls
    with patch('app.api.webhooks.ExchangeManager') as mock_exchange_manager:
        # Act
        response = client.post(webhook_url, json=webhook_payload)

    # Assert
    assert response.status_code == 200
    assert "group_id" in response.json()

    # Verify database state
    position_group = db_session.query(PositionGroup).one_or_none()
    assert position_group is not None
    assert position_group.user_id == test_user.id
    assert position_group.symbol == "BTC/USDT"
    assert position_group.status == "live"

    dca_orders = db_session.query(DCAOrder).all()
    assert len(dca_orders) > 0

