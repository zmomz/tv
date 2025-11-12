from fastapi import APIRouter, Request, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from ..services.signal_processor import process_signal as process_signal_service
from ..services.position_manager import PositionGroupManager
from ..services.exchange_manager import ExchangeManager
from ..services.pool_manager import ExecutionPoolManager, get_pool_manager
from ..services.queue_manager import QueueManager, get_queue_manager
from ..core.config import settings
from ..db.session import get_db
from ..models import models
from ..models.user_models import User
from ..models.key_models import ExchangeConfig
import uuid

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

@router.post("/webhook/{user_id:uuid}")
async def receive_webhook(
    user_id: uuid.UUID,
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

    # --- User and Exchange Config Lookup ---
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        await log_webhook(payload=payload, status="error", error_message=f"User not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")

    # The signature verification should be user-specific
    # For now, we'll keep the simple secret check
    if not verify_signature(payload, signature):
        await log_webhook(payload=payload, status="error", error_message="Invalid signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    await log_webhook(payload=payload, status="received")
    
    try:
        processed_signal = process_signal_service(payload)
        exchange_name = processed_signal.get("exchange")

        if processed_signal['classification'] == 'new_entry':
            # Look up the specific exchange configuration for this user
            exchange_config = db.query(ExchangeConfig).filter(
                ExchangeConfig.user_id == user.id,
                ExchangeConfig.exchange_name == exchange_name,
                ExchangeConfig.is_enabled == True
            ).first()

            if not exchange_config:
                error_msg = f"Active exchange config not found for user {user.id} and exchange {exchange_name}"
                await log_webhook(payload=payload, status="error", error_message=error_msg)
                raise HTTPException(status_code=404, detail=error_msg)

            if pool_manager.can_open_position(user.id):
                async with ExchangeManager(db=db, user_id=user.id, exchange_name=exchange_name) as exchange_manager:
                    position_manager = PositionGroupManager(db=db, exchange_manager=exchange_manager)
                    # Note: The signature for create_group might need to be updated
                    # It previously expected an api_key.id which is no longer relevant in this context
                    new_group = await position_manager.create_group(processed_signal, user.id, exchange_config.id)
                    print(f"Created new position group: {new_group.id}")
                    return {"status": "success", "message": "Position group created and pending execution", "group_id": new_group.id}
            else:
                queued_signal = queue_manager.add_to_queue(WebhookPayload(**payload), user.id)
                print(f"Added signal to queue: {queued_signal.id}")
                return {"status": "success", "message": "Signal queued", "queued_signal_id": queued_signal.id}

    except ValueError as e:
        await log_webhook(payload=payload, status="error", error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "success", "message": "Webhook received and processed"}