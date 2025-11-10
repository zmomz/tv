from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class ExchangeConfigCreate(BaseModel):
    exchange_name: str
    mode: str
    api_key: str
    api_secret: str

class ExchangeConfigOut(BaseModel):
    id: UUID
    user_id: UUID
    exchange_name: str
    mode: str
    is_enabled: bool
    is_validated: bool
    last_validated: datetime = None
    created_at: datetime

    class Config:
        orm_mode = True
