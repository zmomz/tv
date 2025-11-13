import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from datetime import datetime
import uuid

from app.models.user_models import User
from app.models.key_models import APIKey, ExchangeConfig
from app.models.trading_models import PositionGroup, Pyramid, DCAOrder, QueuedSignal
from app.models.risk_analytics_models import RiskAction

# Fixtures are removed as they cause issues with pytest-asyncio fixture resolution.
# Objects will be created directly in the test functions.

@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    async for session in db_session:
        user = User(email="test@example.com", username="testuser", password_hash="password")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is True

@pytest.mark.asyncio
async def test_create_api_key(db_session: AsyncSession):
    async for session in db_session:
        user = User(email="test_api@example.com", username="test_api_user", password_hash="password")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        api_key = APIKey(
            user_id=user.id,
            key_hash="hashed_api_key_value",
            label="My Test API Key"
        )
        session.add(api_key)
        await session.commit()
        await session.refresh(api_key)

        assert api_key.id is not None
        assert api_key.user_id == user.id
        assert api_key.key_hash == "hashed_api_key_value"
        assert api_key.label == "My Test API Key"
        assert api_key.is_active is True

@pytest.mark.asyncio
async def test_create_position_group(db_session: AsyncSession):
    async for session in db_session:
        user = User(email="pg_user@example.com", username="pg_user", password_hash="password")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        config = ExchangeConfig(
            user_id=user.id,
            exchange_name="binance",
            api_key_encrypted="test_key",
            api_secret_encrypted="test_secret"
        )
        session.add(config)
        await session.commit()
        await session.refresh(config)

        pg = PositionGroup(
            user_id=user.id,
            exchange_config_id=config.id,
            exchange="binance",
            symbol="BTCUSDT",
            timeframe=15,
            side="long",
            total_dca_legs=5,
            base_entry_price=Decimal("50000.00"),
            weighted_avg_entry=Decimal("50000.00"),
            tp_mode="per_leg"
        )
        session.add(pg)
        await session.commit()
        await session.refresh(pg)

        assert pg.id is not None
        assert pg.status == "waiting"
        assert pg.symbol == "BTCUSDT"

@pytest.mark.asyncio
async def test_create_pyramid(db_session: AsyncSession):
    async for session in db_session:
        user = User(email="pyr_user@example.com", username="pyr_user", password_hash="password")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        config = ExchangeConfig(
            user_id=user.id,
            exchange_name="binance",
            api_key_encrypted="test_key",
            api_secret_encrypted="test_secret"
        )
        session.add(config)
        await session.commit()
        await session.refresh(config)

        pg = PositionGroup(
            user_id=user.id,
            exchange_config_id=config.id,
            exchange="binance",
            symbol="BTCUSDT",
            timeframe=15,
            side="long",
            total_dca_legs=5,
            base_entry_price=Decimal("50000.00"),
            weighted_avg_entry=Decimal("50000.00"),
            tp_mode="per_leg"
        )
        session.add(pg)
        await session.commit()
        await session.refresh(pg)

        pyramid = Pyramid(
            group_id=pg.id,
            pyramid_index=0,
            entry_price=Decimal("50000.00"),
            entry_timestamp=datetime.utcnow(),
            dca_config={'gap_percent': 0, 'weight_percent': 20, 'tp_percent': 1.0}
        )
        session.add(pyramid)
        await session.commit()
        await session.refresh(pyramid)

        assert pyramid.id is not None
        assert pyramid.status == "pending"
        assert pyramid.group_id == pg.id

@pytest.mark.asyncio
async def test_create_dca_order(db_session: AsyncSession):
    async for session in db_session:
        user = User(email="dca_user@example.com", username="dca_user", password_hash="password")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        config = ExchangeConfig(
            user_id=user.id,
            exchange_name="binance",
            api_key_encrypted="test_key",
            api_secret_encrypted="test_secret"
        )
        session.add(config)
        await session.commit()
        await session.refresh(config)

        pg = PositionGroup(
            user_id=user.id,
            exchange_config_id=config.id,
            exchange="binance",
            symbol="BTCUSDT",
            timeframe=15,
            side="long",
            total_dca_legs=5,
            base_entry_price=Decimal("50000.00"),
            weighted_avg_entry=Decimal("50000.00"),
            tp_mode="per_leg"
        )
        session.add(pg)
        await session.commit()
        await session.refresh(pg)

        pyramid = Pyramid(
            group_id=pg.id,
            pyramid_index=0,
            entry_price=Decimal("50000.00"),
            entry_timestamp=datetime.utcnow(),
            dca_config={'gap_percent': 0, 'weight_percent': 20, 'tp_percent': 1.0}
        )
        session.add(pyramid)
        await session.commit()
        await session.refresh(pyramid)

        dca = DCAOrder(
            group_id=pg.id,
            pyramid_id=pyramid.id,
            leg_index=0,
            symbol="BTCUSDT",
            side="buy",
            order_type="limit",
            price=Decimal("50000.00"),
            quantity=Decimal("0.01"),
            gap_percent=Decimal("0"),
            weight_percent=Decimal("20"),
            tp_percent=Decimal("1"),
            tp_price=Decimal("50500.00")
        )
        session.add(dca)
        await session.commit()
        await session.refresh(dca)
        assert dca.id is not None
        assert dca.status == "pending"
        assert dca.group_id == pg.id

@pytest.mark.asyncio
async def test_create_queued_signal(db_session: AsyncSession):
    async for session in db_session:
        user = User(email="q_user@example.com", username="q_user", password_hash="password")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        qs = QueuedSignal(
            user_id=user.id,
            exchange="binance",
            symbol="BTCUSDT",
            timeframe=15,
            side="long",
            entry_price=Decimal("51000.00"),
            signal_payload={"key": "value"}
        )
        session.add(qs)
        await session.commit()
        await session.refresh(qs)
        assert qs.id is not None
        assert qs.status == "queued"
        assert qs.symbol == "BTCUSDT"

@pytest.mark.asyncio
async def test_create_risk_action(db_session: AsyncSession):
    async for session in db_session:
        user = User(email="risk_user@example.com", username="risk_user", password_hash="password")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        config = ExchangeConfig(
            user_id=user.id,
            exchange_name="binance",
            api_key_encrypted="test_key",
            api_secret_encrypted="test_secret"
        )
        session.add(config)
        await session.commit()
        await session.refresh(config)

        loser_pg = PositionGroup(
            user_id=user.id,
            exchange_config_id=config.id,
            exchange="binance", symbol="BTCUSDT", timeframe=15, side="long",
            total_dca_legs=5, base_entry_price=Decimal("50000"), weighted_avg_entry=Decimal("50000"),
            tp_mode="per_leg", status="active"
        )
        session.add(loser_pg)
        await session.commit()
        await session.refresh(loser_pg)

        winner_pg = PositionGroup(
            user_id=user.id,
            exchange_config_id=config.id,
            exchange="binance", symbol="ETHUSDT", timeframe=15, side="long",
            total_dca_legs=5, base_entry_price=Decimal("3000"), weighted_avg_entry=Decimal("3000"),
            tp_mode="per_leg", status="active"
        )
        session.add(winner_pg)
        await session.commit()
        await session.refresh(winner_pg)

        ra = RiskAction(
            group_id=loser_pg.id,
            action_type="offset_loss",
            loser_group_id=loser_pg.id,
            loser_pnl_usd=Decimal("-100.00"),
            winner_details=[{"group_id": str(winner_pg.id), "pnl_usd": "50.00"}]
        )
        session.add(ra)
        await session.commit()
        await session.refresh(ra)
        assert ra.id is not None
        assert ra.action_type == "offset_loss"
        assert ra.loser_group_id == loser_pg.id
