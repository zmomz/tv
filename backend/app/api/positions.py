from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db.session import get_async_db
from ..models.trading_models import PositionGroup
from ..schemas.trading_schemas import PositionGroupOut
from ..middleware.auth_middleware import require_authenticated
from ..schemas.auth_schemas import UserOut
from typing import List
from uuid import UUID

router = APIRouter()

@router.get("", response_model=List[PositionGroupOut])
async def get_all_positions(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserOut = Depends(require_authenticated),
):
    """
    Retrieve all position groups for the authenticated user.
    """
    result = await db.execute(
        select(PositionGroup).where(PositionGroup.user_id == current_user.id)
    )
    return result.scalars().all()

@router.get("/{position_group_id}", response_model=PositionGroupOut)
async def get_position_group(
    position_group_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserOut = Depends(require_authenticated),
):
    """
    Retrieve a specific position group by ID for the authenticated user.
    """
    result = await db.execute(
        select(PositionGroup).where(
            PositionGroup.id == position_group_id,
            PositionGroup.user_id == current_user.id
        )
    )
    position_group = result.scalars().first()
    if not position_group:
        raise HTTPException(status_code=404, detail="Position group not found")
    return position_group
