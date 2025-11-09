from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from app.services.signal_processor import process_signal as process_signal_service

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
    signature: Optional[str] = Header(None)
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
    except ValueError as e:
        await log_webhook(payload=payload, status="error", error_message=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "success", "message": "Webhook received and processed"}
