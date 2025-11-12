from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def get_analytics():
    """
    Placeholder for analytics data.
    """
    return {}
