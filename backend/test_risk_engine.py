import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, init_db_session
from app.models import models
from app.services.risk_engine import RiskEngine
from app.core.config import settings
from datetime import datetime, timedelta

async def main():
    init_db_session()
    db: Session = SessionLocal()
    try:
        # Ensure a dummy user exists for testing
        user = db.query(models.User).filter(models.User.id == 1).first()
        if not user:
            user = models.User(id=1, username="dummy_risk_user", hashed_password="password")
            db.add(user)
            db.commit()
            db.refresh(user)

        # Ensure a dummy API key exists
        api_key = db.query(models.APIKey).filter(models.APIKey.id == 1).first()
        if not api_key:
            api_key = models.APIKey(
                id=1,
                user_id=user.id,
                exchange="binance",
                encrypted_api_key="dummy_key",
                encrypted_secret="dummy_secret"
            )
            db.add(api_key)
            db.commit()
            db.refresh(api_key)

        # Clean up any existing live position groups for this user
        live_groups = db.query(models.PositionGroup).filter(
            models.PositionGroup.user_id == user.id,
            models.PositionGroup.status == "Live"
        ).all()
        for group in live_groups:
            db.query(models.Pyramid).filter(models.Pyramid.position_group_id == group.id).delete()
            db.delete(group)
        db.commit()

        risk_engine = RiskEngine(db=db)

        # Test should_activate method
        # Create a position group that should activate the risk engine
        losing_group_1 = models.PositionGroup(
            user_id=user.id,
            api_key_id=api_key.id,
            pair="BTCUSDT",
            timeframe="1h",
            status="Live",
            unrealized_pnl_percent=settings.RISK_LOSS_THRESHOLD_PERCENT - 1.0 # 1% below threshold
        )
        db.add(losing_group_1)
        db.commit()
        db.refresh(losing_group_1)

        should_activate = risk_engine.should_activate(losing_group_1)
        print(f"Should activate risk engine for losing group 1: {should_activate}")
        assert should_activate is True

        # Create a position group that should NOT activate the risk engine
        winning_group = models.PositionGroup(
            user_id=user.id,
            api_key_id=api_key.id,
            pair="ETHUSDT",
            timeframe="1h",
            status="Live",
            unrealized_pnl_percent=settings.RISK_LOSS_THRESHOLD_PERCENT + 1.0 # 1% above threshold
        )
        db.add(winning_group)
        db.commit()
        db.refresh(winning_group)

        should_activate_winning = risk_engine.should_activate(winning_group)
        print(f"Should activate risk engine for winning group: {should_activate_winning}")
        assert should_activate_winning is False

        # Test select_losing_group method
        # Create more losing groups for sorting test
        losing_group_2 = models.PositionGroup(
            user_id=user.id,
            api_key_id=api_key.id,
            pair="LTCUSDT",
            timeframe="1h",
            status="Live",
            unrealized_pnl_percent=settings.RISK_LOSS_THRESHOLD_PERCENT - 2.0, # Even worse PnL %
            unrealized_pnl_usd=-200.0,
            created_at=datetime.utcnow() - timedelta(minutes=10) # Older
        )
        db.add(losing_group_2)
        db.commit()
        db.refresh(losing_group_2)

        losing_group_3 = models.PositionGroup(
            user_id=user.id,
            api_key_id=api_key.id,
            pair="XRPUSDT",
            timeframe="1h",
            status="Live",
            unrealized_pnl_percent=settings.RISK_LOSS_THRESHOLD_PERCENT - 1.5, # In between PnL %
            unrealized_pnl_usd=-150.0,
            created_at=datetime.utcnow() - timedelta(minutes=5) # Newer than group 2, older than group 1
        )
        db.add(losing_group_3)
        db.commit()
        db.refresh(losing_group_3)

        # Update losing_group_1 with some USD loss and older timestamp for sorting
        losing_group_1.unrealized_pnl_usd = -100.0
        losing_group_1.created_at = datetime.utcnow() - timedelta(minutes=15) # Oldest
        db.commit()
        db.refresh(losing_group_1)

        selected_losing_group = risk_engine.select_losing_group(user.id)
        print(f"Selected losing group ID: {selected_losing_group.id if selected_losing_group else None}")
        # Expected order: losing_group_2 (worst %), then losing_group_3 (next worst %), then losing_group_1 (oldest if % is same)
        # Since % are different, it should pick losing_group_2 first.
        assert selected_losing_group is not None
        assert selected_losing_group.id == losing_group_2.id

        # Test calculate_required_usd method
        required_usd = risk_engine.calculate_required_usd(losing_group_2)
        print(f"Required USD for losing group 2: {required_usd}")
        assert required_usd == 200.0

        # Test with a group that has no loss
        required_usd_no_loss = risk_engine.calculate_required_usd(winning_group)
        print(f"Required USD for winning group (no loss): {required_usd_no_loss}")
        assert required_usd_no_loss == 0.0

        # Test select_winning_groups method
        # Create multiple winning groups
        winning_group_1 = models.PositionGroup(
            user_id=user.id,
            api_key_id=api_key.id,
            pair="SOLUSDT",
            timeframe="1h",
            status="Live",
            unrealized_pnl_percent=5.0,
            unrealized_pnl_usd=500.0,
            created_at=datetime.utcnow() - timedelta(minutes=20)
        )
        db.add(winning_group_1)
        db.commit()
        db.refresh(winning_group_1)

        winning_group_2 = models.PositionGroup(
            user_id=user.id,
            api_key_id=api_key.id,
            pair="AVAXUSDT",
            timeframe="1h",
            status="Live",
            unrealized_pnl_percent=3.0,
            unrealized_pnl_usd=300.0,
            created_at=datetime.utcnow() - timedelta(minutes=18)
        )
        db.add(winning_group_2)
        db.commit()
        db.refresh(winning_group_2)

        winning_group_3 = models.PositionGroup(
            user_id=user.id,
            api_key_id=api_key.id,
            pair="DOTUSDT",
            timeframe="1h",
            status="Live",
            unrealized_pnl_percent=7.0,
            unrealized_pnl_usd=700.0,
            created_at=datetime.utcnow() - timedelta(minutes=16)
        )
        db.add(winning_group_3)
        db.commit()
        db.refresh(winning_group_3)

        winning_group_4 = models.PositionGroup(
            user_id=user.id,
            api_key_id=api_key.id,
            pair="MATICUSDT",
            timeframe="1h",
            status="Live",
            unrealized_pnl_percent=2.0,
            unrealized_pnl_usd=200.0,
            created_at=datetime.utcnow() - timedelta(minutes=14)
        )
        db.add(winning_group_4)
        db.commit()
        db.refresh(winning_group_4)

        selected_winning_groups = risk_engine.select_winning_groups(user.id, required_usd)
        print(f"Selected winning group IDs: {[g.id for g in selected_winning_groups]}")
        assert len(selected_winning_groups) <= 3
        # Expected order: winning_group_3 (700), winning_group_1 (500), winning_group_2 (300)
        assert selected_winning_groups[0].id == winning_group_3.id
        assert selected_winning_groups[1].id == winning_group_1.id
        assert selected_winning_groups[2].id == winning_group_2.id

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
