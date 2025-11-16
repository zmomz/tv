from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.session import get_async_db
from ..schemas.trading_schemas import SignalPayload
from ..services.webhook_service import process_webhook_signal
from ..services.jwt_service import verify_webhook_token
from ..services.exchange_manager import ExchangeManager
from ..models.trading_models import PositionGroup, PositionGroupStatus
from ..core.config import settings
from uuid import UUID

router = APIRouter()

@router.post("/webhook/{user_id}", status_code=status.HTTP_200_OK)
async def receive_webhook(
    user_id: UUID,
    webhook_signal: SignalPayload,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Receives and processes webhook signals from TradingView.
    """
    # 1. Verify the webhook token
    if webhook_signal.secret != settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")

    # 2. Process the signal
    try:
        result = await process_webhook_signal(db, user_id, webhook_signal.tv, webhook_signal.execution_intent)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing webhook: {e}")

@router.post("/test-signal/{user_id}", status_code=status.HTTP_200_OK)
async def test_signal(
    user_id: UUID,
    signal_payload: SignalPayload,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Test endpoint to simulate a webhook signal without requiring a valid webhook secret.
    """
    try:
        result = await process_webhook_signal(db, user_id, signal_payload.tv, signal_payload.execution_intent)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing test signal: {e}")