from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..db.session import get_db
from ..models import trading_models as models
from pydantic import BaseModel

router = APIRouter()

class PositionGroup(BaseModel):
    id: int
    pair: str
    status: str
    unrealized_pnl_percent: float

    class Config:
        orm_mode = True

@router.get("/position_groups", response_model=List[PositionGroup])
async def get_position_groups(db: Session = Depends(get_db)):
    return db.query(models.PositionGroup).all()
