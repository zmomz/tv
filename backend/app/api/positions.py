from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..schemas.trading_schemas import PositionGroupOut
from ..services.position_manager import PositionGroupManager
from typing import List

router = APIRouter()

@router.get("", response_model=List[PositionGroupOut])
async def get_positions(
    db: Session = Depends(get_db),
):
    """
    Get all positions.
    """
    return db.query(PositionGroup).all()
