import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, init_db_session
from app.models import models
from app.services.queue_manager import QueueManager
from app.services.signal_processor import process_signal as process_signal_service

async def main():
    init_db_session()
    db: Session = SessionLocal()
    try:
        # Ensure a dummy user exists for testing
        user = db.query(models.User).filter(models.User.id == 1).first()
        if not user:
            user = models.User(id=1, username="dummy_queue_user", hashed_password="password")
            db.add(user)
            db.commit()
            db.refresh(user)

        # Clean up any existing queued signals for this user
        db.query(models.QueuedSignal).filter(models.QueuedSignal.user_id == user.id).delete()
        db.commit()

        queue_manager = QueueManager(db=db)

        # Raw signal payloads
        raw_signal1_payload = {"secret": "test", "tv": {"exchange": "BINANCE", "symbol": "BTCUSDT", "action": "buy"}, "execution_intent": {"type": "signal", "side": "buy"}}
        raw_signal2_payload = {"secret": "test", "tv": {"exchange": "BINANCE", "symbol": "ETHUSDT", "action": "buy"}, "execution_intent": {"type": "signal", "side": "buy"}}
        raw_signal3_payload = {"secret": "test", "tv": {"exchange": "BINANCE", "symbol": "ADAUSDT", "action": "buy"}, "execution_intent": {"type": "signal", "side": "buy"}}

        # Process signals before adding to queue
        processed_signal1 = process_signal_service(raw_signal1_payload)
        processed_signal2 = process_signal_service(raw_signal2_payload)
        processed_signal3 = process_signal_service(raw_signal3_payload)

        queued_signal1 = queue_manager.add_to_queue(processed_signal1, user.id)
        await asyncio.sleep(0.01) # Ensure different created_at timestamps
        queued_signal2 = queue_manager.add_to_queue(processed_signal2, user.id)
        await asyncio.sleep(0.01)
        queued_signal3 = queue_manager.add_to_queue(processed_signal3, user.id)

        print(f"Queued Signal 1 ID: {queued_signal1.id}")
        print(f"Queued Signal 2 ID: {queued_signal2.id}")
        print(f"Queued Signal 3 ID: {queued_signal3.id}")

        # Test promote_next (should return the oldest, which is signal1)
        next_signal = queue_manager.promote_next(user.id)
        print(f"Promoted Signal ID: {next_signal.id if next_signal else None}")
        assert next_signal is not None
        assert next_signal.id == queued_signal1.id

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
