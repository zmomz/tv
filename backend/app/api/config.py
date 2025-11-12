from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..core.config import settings
from ..schemas.config_schemas import AppConfig, AppSettings, ExchangeSettings, ExecutionPoolSettings, GridStrategySettings, RiskEngineSettings
import json

router = APIRouter()

@router.get("", response_model=AppConfig)
async def get_config():
    """
    Get the current application configuration.
    """
    return AppConfig(
        app=AppSettings(
            mode=settings.APP_MODE,
            data_dir=settings.APP_DATA_DIR,
            log_level=settings.APP_LOG_LEVEL,
        ),
        exchange=ExchangeSettings(
            name=settings.EXCHANGE_NAME,
            api_key=settings.API_KEY,
            api_secret=settings.API_SECRET,
            testnet=settings.EXCHANGE_TESTNET,
            precision_refresh_sec=settings.EXCHANGE_PRECISION_REFRESH_SEC,
        ),
        execution_pool=ExecutionPoolSettings(
            max_open_groups=settings.POOL_MAX_OPEN_GROUPS,
            count_pyramids=settings.POOL_COUNT_PYRAMIDS,
        ),
        grid_strategy=GridStrategySettings(
            dca_config={},  # Populate as needed
            tp_config={},   # Populate as needed
        ),
        risk_engine=RiskEngineSettings(
            loss_threshold_percent=settings.RISK_LOSS_THRESHOLD_PERCENT,
            require_full_pyramids=settings.RISK_REQUIRE_FULL_PYRAMIDS,
            post_full_wait_minutes=settings.RISK_POST_FULL_WAIT_MINUTES,
        ),
    )

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
