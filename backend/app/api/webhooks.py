from fastapi import APIRouter, Request, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.services.signal_processor import process_signal as process_signal_service
from app.services.position_manager import PositionGroupManager
from app.services.exchange_manager import ExchangeManager
from app.services.pool_manager import ExecutionPoolManager, get_pool_manager
from app.services.queue_manager import QueueManager, get_queue_manager
from app.core.config import settings
from app.db.session import get_db
from app.models import models

router = APIRouter()

class WebhookPayload(BaseModel):
    secret: str
    tv: dict
    execution_intent: dict

# For now, a simple hardcoded secret for demonstration
WEBHOOK_SECRET = "test"

def verify_signature(payload: dict, signature: Optional[str]) -> bool:
    # In a real application, this would involve cryptographic signature verification.
    # For now, we'll just check a simple secret in the payload.
    return payload.get("secret") == WEBHOOK_SECRET

async def log_webhook(payload: dict, status: str, error_message: Optional[str] = None):
    # TODO: Implement actual logging to the database
    print(f"Webhook Log - Status: {status}, Payload: {payload}, Error: {error_message}")

@router.post("/webhook")
async def receive_webhook(
    request: Request,
    signature: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    pool_manager: ExecutionPoolManager = Depends(get_pool_manager),
    queue_manager: QueueManager = Depends(get_queue_manager)
):
    try:
        payload = await request.json()
    except Exception as e:
        await log_webhook(payload={}, status="error", error_message=f"Invalid JSON payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if not verify_signature(payload, signature):
        await log_webhook(payload=payload, status="error", error_message="Invalid signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    await log_webhook(payload=payload, status="received")
    
    try:
        processed_signal = process_signal_service(payload)
        print(f"Processed Signal: {processed_signal}")

        if processed_signal['classification'] == 'new_entry':
            # Get or create a dummy user
            user = db.query(models.User).filter(models.User.id == 1).first()
            if not user:
                user = models.User(id=1, username="dummy", hashed_password="password")
                db.add(user)
                db.commit()
                db.refresh(user)

            # Get or create a dummy API key
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

            if pool_manager.can_open_position(user.id):
                exchange_manager = ExchangeManager(
                    api_key=settings.API_KEY,
                    api_secret=settings.API_SECRET,
                    testnet=settings.EXCHANGE_TESTNET
                )
                position_manager = PositionGroupManager(db=db, exchange_manager=exchange_manager)
                new_group = position_manager.create_group(processed_signal, user.id, api_key.id)
                print(f"Created new position group: {new_group.id}")
                return {"status": "success", "message": "New position opened", "group_id": new_group.id}
            else:
                queued_signal = queue_manager.add_to_queue(processed_signal, user.id)
                print(f"Added signal to queue: {queued_signal.id}")
                return {"status": "success", "message": "Signal queued", "queued_signal_id": queued_signal.id}

    except ValueError as e:
        await log_webhook(payload=payload, status="error", error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "success", "message": "Webhook received and processed"}
