from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..core.config import settings
from ..schemas.config_schemas import AppConfig
import json

router = APIRouter()

@router.get("", response_model=AppConfig)
async def get_config():
    """
    Get the current application configuration.
    """
    return settings

@router.put("", response_model=AppConfig)
async def update_config(
    config: AppConfig,
    db: Session = Depends(get_db),
):
    """
    Update the application configuration.
    """
    with open("engine_data/config.json", "w") as f:
        json.dump(config.dict(), f, indent=4)
    
    # In a real-world application, you would trigger a hot-reload of the
    # engine settings here. For now, we'll just return the new config.
    return config
