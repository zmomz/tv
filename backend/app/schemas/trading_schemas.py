from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class SignalPayload(BaseModel):
    secret: str
    tv: dict
    execution_intent: dict

class PositionGroupOut(BaseModel):
    id: UUID
    user_id: UUID
    exchange: str
    symbol: str
    status: str
    entry_price: Optional[float]
    current_price: Optional[float]
    pnl: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
