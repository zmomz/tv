import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, init_db_session
from app.models import models
from app.services.pool_manager import ExecutionPoolManager
from app.core.config import settings

async def main():
    init_db_session()
    db: Session = SessionLocal()
    try:
        # Ensure a dummy user exists for testing
        user = db.query(models.User).filter(models.User.id == 1).first()
        if not user:
            user = models.User(id=1, username="dummy_pool_user", hashed_password="password")
            db.add(user)
            db.commit()
            db.refresh(user)

        # Clean up any existing live position groups for this user
        live_groups = db.query(models.PositionGroup).filter(
            models.PositionGroup.user_id == user.id,
            models.PositionGroup.status == "Live"
        ).all()
        for group in live_groups:
            db.query(models.Pyramid).filter(models.Pyramid.position_group_id == group.id).delete()
            db.delete(group)
        db.commit()

        pool_manager = ExecutionPoolManager(db=db)

        # Test initial state (assuming no open groups for this user)
        open_slots = pool_manager.get_open_slots(user.id)
        can_open = pool_manager.can_open_position(user.id)
        print(f"Initial open slots for user {user.id}: {open_slots}")
        print(f"Can open position for user {user.id}: {can_open}")
        assert open_slots == settings.POOL_MAX_OPEN_GROUPS
        assert can_open is True

        # Create a dummy API key if it doesn't exist
        dummy_api_key = db.query(models.APIKey).filter(models.APIKey.id == 1).first()
        if not dummy_api_key:
            dummy_api_key = models.APIKey(
                id=1,
                user_id=user.id,
                exchange="binance",
                encrypted_api_key="dummy_key",
                encrypted_secret="dummy_secret"
            )
            db.add(dummy_api_key)
            db.commit()
            db.refresh(dummy_api_key)

        # Create a dummy position group
        new_group = models.PositionGroup(
            user_id=user.id,
            api_key_id=dummy_api_key.id,
            pair="ETHUSDT",
            timeframe="1h",
            status="Live"
        )
        db.add(new_group)
        db.commit()
        db.refresh(new_group)

        # Test after creating one group
        open_slots_after = pool_manager.get_open_slots(user.id)
        can_open_after = pool_manager.can_open_position(user.id)
        print(f"Open slots after creating one group: {open_slots_after}")
        print(f"Can open position after creating one group: {can_open_after}")
        assert open_slots_after == settings.POOL_MAX_OPEN_GROUPS - 1
        assert can_open_after is True

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
